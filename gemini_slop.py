import numpy as np
import torch
import torch.nn as nn
from scipy.optimize import linear_sum_assignment
import cv2
from typing import Dict, Tuple

class StoreLayoutOptimizer:
    def __init__(self, tau: float = 0.1, sinkhorn_iters: int = 20):
        self.tau = tau
        self.sinkhorn_iters = sinkhorn_iters
        self.bin_mask = None
        self.item_to_id = {}
        self.id_to_item = {}
        self.shelf_coords = []
        self.B = None
        self.D = None
        self.W = None
        self.is_prepared = False
        self.cached_layout = None

    def load_layout_mask(self, mask_filepath: str):
        self.bin_mask = np.load(mask_filepath)
        y_indices, x_indices = np.where(self.bin_mask == 1)
        self.shelf_coords = list(zip(y_indices, x_indices))

    def load_customer_demands(self, demands_filepath: str):
        raw_baskets = []
        unique_items = set()
        with open(demands_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                clean_line = line.strip().strip(',')
                if clean_line:
                    items = [item.strip() for item in clean_line.split(',')]
                    raw_baskets.append(items)
                    unique_items.update(items)

        sorted_items = sorted(list(unique_items))
        self.item_to_id = {item: idx for idx, item in enumerate(sorted_items)}
        self.id_to_item = {idx: item for idx, item in enumerate(sorted_items)}
        
        num_customers, num_items = len(raw_baskets), len(sorted_items)
        B_np = np.zeros((num_customers, num_items), dtype=np.float32)
        for cust_idx, basket in enumerate(raw_baskets):
            for item in basket:
                if item in self.item_to_id:
                    B_np[cust_idx, self.item_to_id[item]] = 1.0
        self.B = torch.tensor(B_np)

    def prepare_optimization(self):
        num_items = len(self.item_to_id)
        active_shelves = np.array(self.shelf_coords[:num_items]) 
        
        y_diff = np.abs(active_shelves[:, 0:1] - active_shelves[:, 0:1].T)
        x_diff = np.abs(active_shelves[:, 1:2] - active_shelves[:, 1:2].T)
        self.D = torch.tensor((y_diff + x_diff).astype(np.float32))
        
        self.W = nn.Parameter(torch.randn(num_items, num_items, requires_grad=True))
        self.is_prepared = True

    def _sinkhorn(self, W: torch.Tensor) -> torch.Tensor:
        Z = W / self.tau
        for _ in range(self.sinkhorn_iters):
            Z = Z - torch.logsumexp(Z, dim=-1, keepdim=True)
            Z = Z - torch.logsumexp(Z, dim=-2, keepdim=True)
        return torch.exp(Z)

    def train(self, epochs: int = 10, lr: float = 0.1):
        """Trains the model to find the optimal layout."""
        optimizer = torch.optim.Adam([self.W], lr=lr)
        for _ in range(epochs):
            optimizer.zero_grad()
            M_soft = self._sinkhorn(self.W)
            L = torch.matmul(self.B, M_soft)
            loss = ((torch.matmul(L, self.D) * L).sum(dim=-1) / 2.0).mean()
            loss.backward()
            optimizer.step()

        # Cache layout after training so we don't recalculate per API request
        with torch.no_grad():
            M_soft = self._sinkhorn(self.W).cpu().numpy()
        item_indices, shelf_indices = linear_sum_assignment(-M_soft)
        self.cached_layout = {self.id_to_item[i]: self.shelf_coords[s] for i, s in zip(item_indices, shelf_indices)}

    def _item_icon(self, item: str, size: int) -> np.ndarray:
        icon = np.ones((size, size, 3), dtype=np.uint8) * 255
        color = (
            (hash(item) & 0xFF),
            ((hash(item) >> 8) & 0xFF),
            ((hash(item) >> 16) & 0xFF),
        )
        cv2.circle(icon, (size // 2, size // 2), size // 2 - 2, color, -1)
        cv2.circle(icon, (size // 2, size // 2), size // 2 - 2, (0, 0, 0), 1)
        letter = item[0].upper()
        font_scale = 0.4
        (tw, th), _ = cv2.getTextSize(letter, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        tx = (size - tw) // 2
        ty = (size + th) // 2
        cv2.putText(icon, letter, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1)
        return icon

    def generate_and_save_map(self, basket_items: list, output_filename: str = "empty_map.png"):
        """Draws the store, highlights the requested items, and saves it to disk."""
        if not self.cached_layout:
            return
            
        cell_size = 30
        h, w = self.bin_mask.shape
        # Create white background
        img = np.ones((h * cell_size, w * cell_size, 3), dtype=np.uint8) * 255
        
        # Draw shelves as gray boxes
        for y in range(h):
            for x in range(w):
                if self.bin_mask[y, x] == 1:
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (200, 200, 200), -1)
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (150, 150, 150), 1)

        # Overlay an icon for each requested item
        icon_size = cell_size - 4
        for item in basket_items:
            if item in self.cached_layout:
                y, x = self.cached_layout[item]
                icon = self._item_icon(item, icon_size)
                ox = x * cell_size + 2
                oy = y * cell_size + 2
                img[oy:oy + icon_size, ox:ox + icon_size] = icon

        # Save to disk so the Flask backend can read it!
        cv2.imwrite(output_filename, img)