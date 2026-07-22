import os
import numpy as np
import torch
import torch.nn as nn
from scipy.optimize import linear_sum_assignment
import cv2
from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFont

class StoreLayoutOptimizer:
    def __init__(self, tau: float = 0.1, sinkhorn_iters: int = 20):
        self.tau = tau
        self.sinkhorn_iters = sinkhorn_iters
        
        # Raw Data Storage (Loaded once at startup)
        self.bin_mask = None
        self.shelf_coords = []
        self.raw_baskets = []
        
        # Dynamic Subset Data (Built per request)
        self.item_to_id = {}
        self.id_to_item = {}
        self.B = None
        self.shelf_x = None
        self.shelf_y = None
        self.W = None
        self.cached_layout = None

    def load_layout_mask(self, mask_filepath: str):
        """Loads physical store layout into memory."""
        self.bin_mask = np.load(mask_filepath)
        y_indices, x_indices = np.where(self.bin_mask == 1)
        self.shelf_coords = list(zip(y_indices, x_indices))

    def load_customer_demands(self, demands_filepath: str):
        """Loads all historical baskets into memory (List of Lists), no tensors yet."""
        self.raw_baskets = []
        with open(demands_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                clean_line = line.strip().strip(',')
                if clean_line:
                    items = [item.strip() for item in clean_line.split(',')]
                    self.raw_baskets.append(items)

    def _sinkhorn(self, W: torch.Tensor) -> torch.Tensor:
        Z = W / self.tau
        for _ in range(self.sinkhorn_iters):
            Z = Z - torch.logsumexp(Z, dim=-1, keepdim=True)
            Z = Z - torch.logsumexp(Z, dim=-2, keepdim=True)
        return torch.exp(Z)

    def _compute_bbox_loss(self, M: torch.Tensor, bbox_tau: float = 0.5) -> torch.Tensor:
        item_x = torch.matmul(M, self.shelf_x)
        item_y = torch.matmul(M, self.shelf_y)

        item_x_expanded = item_x.unsqueeze(0) 
        item_y_expanded = item_y.unsqueeze(0) 

        mask_max = (1.0 - self.B) * -1e4
        mask_min = (1.0 - self.B) * 1e4

        max_x = bbox_tau * torch.logsumexp((item_x_expanded + mask_max) / bbox_tau, dim=1)
        min_x = -bbox_tau * torch.logsumexp(-(item_x_expanded + mask_min) / bbox_tau, dim=1)
        
        max_y = bbox_tau * torch.logsumexp((item_y_expanded + mask_max) / bbox_tau, dim=1)
        min_y = -bbox_tau * torch.logsumexp(-(item_y_expanded + mask_min) / bbox_tau, dim=1)

        return (max_x - min_x + max_y - min_y).mean()

    def optimize_for_subset(self, subset_items: list, epochs: int = 150, lr: float = 0.1):
        """
        Dynamically builds tensors and trains layout exclusively for the submitted items.
        """
        # 1. Setup dictionaries for the subset
        unique_subset = sorted(list(set(subset_items)))
        num_items = len(unique_subset)
        
        if num_items == 0:
            self.cached_layout = {}
            return
            
        self.item_to_id = {item: idx for idx, item in enumerate(unique_subset)}
        self.id_to_item = {idx: item for idx, item in enumerate(unique_subset)}

        # 2. Build B Matrix: Filter historical baskets to only include subset items
        subset_baskets = []
        for basket in self.raw_baskets:
            # Find intersection of customer's cart and the requested subset
            intersection = [item for item in basket if item in self.item_to_id]
            if intersection: # Only keep customers who actually bought at least one subset item
                subset_baskets.append(intersection)
                
        num_customers = max(len(subset_baskets), 1) # Prevent empty matrix crash
        B_np = np.zeros((num_customers, num_items), dtype=np.float32)
        
        for cust_idx, basket in enumerate(subset_baskets):
            for item in basket:
                B_np[cust_idx, self.item_to_id[item]] = 1.0
                
        self.B = torch.tensor(B_np)

        # 3. Assign physical shelves (Grab exactly N shelf slots for N subset items)
        active_shelves = np.array(self.shelf_coords[:num_items]) 
        self.shelf_y = torch.tensor(active_shelves[:, 0], dtype=torch.float32)
        self.shelf_x = torch.tensor(active_shelves[:, 1], dtype=torch.float32)
        
        # 4. Initialize learnable parameters for THIS specific subset
        self.W = nn.Parameter(torch.randn(num_items, num_items, requires_grad=True))

        # 5. Fast Training Loop
        optimizer = torch.optim.Adam([self.W], lr=lr)
        for _ in range(epochs):
            optimizer.zero_grad()
            M_soft = self._sinkhorn(self.W)
            loss = self._compute_bbox_loss(M_soft)
            loss.backward()
            optimizer.step()

        # 6. Cache layout via Hungarian Matching
        with torch.no_grad():
            M_soft = self._sinkhorn(self.W).cpu().numpy()
            
        item_indices, shelf_indices = linear_sum_assignment(-M_soft)
        self.cached_layout = {self.id_to_item[i]: self.shelf_coords[s] for i, s in zip(item_indices, shelf_indices)}

    def _load_product_image(self, item: str, size: int) -> Image.Image:
        name = item.lower().replace(" ", "_").replace("/", "_")
        assets_dir = getattr(self, "assets_dir", "assets")
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join(assets_dir, name + ext)
            if os.path.isfile(path):
                img = Image.open(path).convert("RGB")
                return img.resize((size, size), Image.LANCZOS)
        icon = Image.new("RGB", (size, size), (255, 255, 255))
        draw = ImageDraw.Draw(icon)
        color = (
            (hash(item) & 0xFF),
            ((hash(item) >> 8) & 0xFF),
            ((hash(item) >> 16) & 0xFF),
        )
        draw.ellipse([2, 2, size - 2, size - 2], fill=color, outline=(0, 0, 0))
        letter = item[0].upper()
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size - 8)
        except (IOError, OSError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) // 2 - bbox[0]
        ty = (size - th) // 2 - bbox[1]
        draw.text((tx, ty), letter, font=font, fill=(255, 255, 255))
        return icon

    def generate_and_save_map(self, basket_items: list, output_filename: str = "empty_map.png", assets_dir: str = "assets"):
        if not self.cached_layout:
            return
        self.assets_dir = assets_dir

        cell_size = 30
        h, w = self.bin_mask.shape
        img = np.ones((h * cell_size, w * cell_size, 3), dtype=np.uint8) * 255

        for y in range(h):
            for x in range(w):
                if self.bin_mask[y, x] == 1:
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (200, 200, 200), -1)
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (150, 150, 150), 1)

        icon_size = cell_size - 4
        for item in basket_items:
            if item in self.cached_layout:
                y, x = self.cached_layout[item]
                pil_icon = self._load_product_image(item, icon_size)
                icon_np = np.array(pil_icon)
                ox = x * cell_size + 2
                oy = y * cell_size + 2
                img[oy:oy + icon_size, ox:ox + icon_size] = icon_np

        cv2.imwrite(output_filename, img)