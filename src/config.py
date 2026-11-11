"""Configuration management"""

import os
from typing import Dict


class ConfigManager:
    """Manage API configuration and model pricing"""

    @staticmethod
    def get_nebius_config() -> Dict:
        """Get Nebius Token Factory configuration with accurate pricing"""
        return {
            "api_key": os.getenv("NEBIUS_API_KEY", ""),
            "api_base": "https://api.tokenfactory.nebius.com/v1/",
            # Model pricing and specs from Nebius Token Factory
            "models": {
                "meta-llama/Meta-Llama-3.1-8B-Instruct": {
                    "name": "Meta-Llama-3.1-8B-Instruct",
                    "input_cost_per_1m": 0.02,      # $0.02 per 1M input tokens
                    "output_cost_per_1m": 0.06,     # $0.06 per 1M output tokens
                    "throughput_tok_s": 30,
                    "context_size": 128000,
                    "quantization": "fp8",
                    "description": "Small Llama model with strong reasoning and efficiency"
                },
                "meta-llama/Llama-3.3-70B-Instruct": {
                    "name": "Meta-Llama-3.3-70B-Instruct",
                    "input_cost_per_1m": 0.13,      # $0.13 per 1M input tokens
                    "output_cost_per_1m": 0.40,     # $0.40 per 1M output tokens
                    "throughput_tok_s": 25,
                    "context_size": 128000,
                    "quantization": "fp8",
                    "description": "Refined Llama model with strong reasoning and chat quality"
                },
                "gemma-2-9b-it": {
                    "name": "Gemma-2-9b-it",
                    "input_cost_per_1m": 0.03,      # $0.03 per 1M input tokens
                    "output_cost_per_1m": 0.09,     # $0.09 per 1M output tokens
                    "throughput_tok_s": 90,
                    "context_size": 8000,
                    "quantization": "fp8",
                    "description": "Larger Gemma model with high-quality chat and coding"
                }
            }
        }
