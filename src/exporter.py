"""Export results to Excel format"""

from typing import List
import pandas as pd

from models import GenerationResult


class ExcelExporter:
    """Save results to Excel with proper formatting"""

    @staticmethod
    def export_results(
        results: List[GenerationResult],
        filename: str = "results/generations_with_human_eval.xlsx"
    ):
        """Export results to Excel"""
        df_data = [r.to_dict() for r in results]
        df = pd.DataFrame(df_data)

        # Ensure proper column order
        column_order = [
            'product_name', 'product_attributes', 'material', 'warranty',
            'generated_description', 'latency_ms', 'input_tokens', 'output_tokens', 'cost_usd',
            'fluency', 'grammar', 'tone', 'length', 'grounding', 'latency', 'cost',
            'final_score'
        ]

        # Add missing columns
        for col in column_order:
            if col not in df.columns:
                df[col] = None

        df = df[column_order]

        # Write to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)

        return df
