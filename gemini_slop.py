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
        
        # PyTorch Data
        self.B = None
        self.shelf_x = None  # Replaces D matrix
        self.shelf_y = None  # Replaces D matrix
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
        
        # Extract distinct X and Y coordinate vectors instead of calculating a massive D matrix
        self.shelf_y = torch.tensor(active_shelves[:, 0], dtype=torch.float32)
        self.shelf_x = torch.tensor(active_shelves[:, 1], dtype=torch.float32)
        
        self.W = nn.Parameter(torch.randn(num_items, num_items, requires_grad=True))
        self.is_prepared = True

    def _sinkhorn(self, W: torch.Tensor) -> torch.Tensor:
        Z = W / self.tau
        for _ in range(self.sinkhorn_iters):
            Z = Z - torch.logsumexp(Z, dim=-1, keepdim=True)
            Z = Z - torch.logsumexp(Z, dim=-2, keepdim=True)
        return torch.exp(Z)

    def _compute_bbox_loss(self, M: torch.Tensor, bbox_tau: float = 0.5) -> torch.Tensor:
        """Calculates the soft bounding box span for all customer baskets."""
        # 1. Map items to their expected physical locations
        # M is shape (N_items, N_shelves) -> gives expected (X, Y) for each item
        item_x = torch.matmul(M, self.shelf_x) # Shape: (N_items,)
        item_y = torch.matmul(M, self.shelf_y) # Shape: (N_items,)

        # Expand shapes for broadcasting to the customer batch
        item_x_expanded = item_x.unsqueeze(0)  # Shape: (1, N_items)
        item_y_expanded = item_y.unsqueeze(0)  # Shape: (1, N_items)

        # 2. Mask out items that the customer did NOT buy.
        # We use +/- 10,000 to push unbought items to extreme values so they 
        # get entirely ignored by the logsumexp (Soft-Max/Soft-Min) functions.
        mask_max = (1.0 - self.B) * -1e4
        mask_min = (1.0 - self.B) * 1e4

        x_for_max = item_x_expanded + mask_max
        x_for_min = item_x_expanded + mask_min
        y_for_max = item_y_expanded + mask_max
        y_for_min = item_y_expanded + mask_min

        # 3. Soft-Max and Soft-Min calculations using logsumexp
        max_x = bbox_tau * torch.logsumexp(x_for_max / bbox_tau, dim=1)
        min_x = -bbox_tau * torch.logsumexp(-x_for_min / bbox_tau, dim=1)
        
        max_y = bbox_tau * torch.logsumexp(y_for_max / bbox_tau, dim=1)
        min_y = -bbox_tau * torch.logsumexp(-y_for_min / bbox_tau, dim=1)

        # 4. Calculate span (perimeter footprint) per customer and average it
        span_x = max_x - min_x
        span_y = max_y - min_y
        
        return (span_x + span_y).mean()

    def train(self, epochs: int = 150, lr: float = 0.1):
        """Trains the model to find the optimal layout."""
        optimizer = torch.optim.Adam([self.W], lr=lr)
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass through Sinkhorn to get soft permutations
            M_soft = self._sinkhorn(self.W)
            
            # Use the new Bounding Box Loss
            loss = self._compute_bbox_loss(M_soft)
            
            # Backpropagation
            loss.backward()
            optimizer.step()

        # Cache layout after training
        with torch.no_grad():
            M_soft = self._sinkhorn(self.W).cpu().numpy()
            
        item_indices, shelf_indices = linear_sum_assignment(-M_soft)
        self.cached_layout = {self.id_to_item[i]: self.shelf_coords[s] for i, s in zip(item_indices, shelf_indices)}

    def generate_and_save_map(self, basket_items: list, output_filename: str = "empty_map.png"):
        """Draws the store, highlights the requested items, and saves it to disk."""
        if not self.cached_layout:
            return
            
        cell_size = 30
        h, w = self.bin_mask.shape
        img = np.ones((h * cell_size, w * cell_size, 3), dtype=np.uint8) * 255
        
        for y in range(h):
            for x in range(w):
                if self.bin_mask[y, x] == 1:
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (200, 200, 200), -1)
                    cv2.rectangle(img, (x*cell_size, y*cell_size), ((x+1)*cell_size, (y+1)*cell_size), (150, 150, 150), 1)

        for item in basket_items:
            if item in self.cached_layout:
                y, x = self.cached_layout[item]
                center = (int((x + 0.5) * cell_size), int((y + 0.5) * cell_size))
                cv2.circle(img, center, cell_size // 3, (0, 0, 255), -1)
                cv2.putText(img, item, (center[0] - 15, center[1] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        cv2.imwrite(output_filename, img)