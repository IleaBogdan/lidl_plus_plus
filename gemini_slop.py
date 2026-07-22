import numpy as np
import os
import random
from collections import Counter

class StoreOptimizationPipeline:
    def __init__(self):
        """Initializes the pipeline with empty states for UI binding."""
        self.store_layout = None
        self.customer_demands = []
        self.item_coordinates = {}  # E.g., {"Bananas": (10, 5), "Whole Milk": (2, 8)}
        # Static store layout: 3 aisles, all sharing the same fixed capacity
        # (0-16 products), generated once for this run.
        aisle_capacity = random.randint(0, 16)
        self.aisle_lengths = [aisle_capacity] * 3

    def arrange_products(self, items: list) -> list:
        """
        Places submitted products into the store's static aisle layout,
        filling each aisle up to its capacity before moving to the next one.
        Items beyond the total aisle capacity are dropped.
        """
        arrangement = []
        index = 0
        for capacity in self.aisle_lengths:
            arrangement.append(items[index:index + capacity])
            index += capacity
        return arrangement

    def load_store_layout(self, filepath_mask: str) -> bool:
        """
        Loads the store layout from a binary numpy mask.
        1 = shelf/obstacle, 0 = walkable path.
        """
        try:
            self.store_layout = np.load(filepath_mask)
            print(f"Successfully loaded store layout with shape: {self.store_layout.shape}")
            return True
        except Exception as e:
            print(f"Error loading store layout: {e}")
            return False

    def load_customer_demands(self, filepath_txt: str) -> bool:
        """
        Loads customer demands from a text file.
        Expects one customer per row, items separated by commas.
        """
        try:
            parsed_demands = []
            with open(filepath_txt, 'r', encoding='utf-8') as file:
                for line in file:
                    # Strip whitespace and trailing commas, then split
                    clean_line = line.strip().strip(',')
                    if clean_line:
                        items = [item.strip() for item in clean_line.split(',')]
                        parsed_demands.append(items)
            
            self.customer_demands = parsed_demands
            print(f"Successfully loaded {len(self.customer_demands)} customer records.")
            return True
        except Exception as e:
            print(f"Error loading customer demands: {e}")
            return False

    def load_item_coordinates(self, coordinate_mapping: dict):
        """
        Injects the missing link: where each item lives on the bin_mask grid.
        This can be passed from the UI or loaded from a separate JSON file.
        """
        self.item_coordinates = coordinate_mapping

    def get_top_items(self, limit: int = 10) -> list:
        """
        Returns the most frequently demanded items.
        Useful for a UI dashboard overview.
        """
        if not self.customer_demands:
            return []
            
        all_items = [item for sublist in self.customer_demands for item in sublist]
        return Counter(all_items).most_common(limit)

    def get_customer_basket(self, customer_index: int) -> list:
        """Retrieves a specific customer's demand list by index."""
        if 0 <= customer_index < len(self.customer_demands):
            return self.customer_demands[customer_index]
        return []

    def calculate_picking_locations(self, customer_index: int) -> list:
        """
        Translates a customer's requested items into physical grid coordinates.
        Requires item_coordinates to be populated.
        """
        basket = self.get_customer_basket(customer_index)
        locations = []
        
        for item in basket:
            if item in self.item_coordinates:
                locations.append({
                    "item": item,
                    "coordinates": self.item_coordinates[item]
                })
            else:
                print(f"Warning: Location for '{item}' not found in mapping.")
                
        return locations

    # --- UI GETTERS ---

    def get_grid_dimensions(self) -> tuple:
        """Returns the (height, width) of the store grid for UI rendering."""
        if self.store_layout is not None:
            return self.store_layout.shape
        return (0, 0)

    def get_walkable_spaces(self) -> list:
        """Returns a list of (y, x) coordinates representing empty aisles."""
        if self.store_layout is not None:
            # Assuming 0 is walkable space
            y_coords, x_coords = np.where(self.store_layout == 0)
            return list(zip(y_coords, x_coords))
        return []