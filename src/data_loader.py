"""Data loading and preparation"""

import csv
from typing import List
from models import Product


class DataLoader:
    """Load and prepare product dataset"""

    @staticmethod
    def load_csv(filepath: str) -> List[Product]:
        """Load products from CSV file"""
        products = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(Product(
                    product_name=row['product_name'],
                    attributes=row['Product_attribute_list'],
                    material=row['material'],
                    warranty=row['warranty']
                ))
        return products
