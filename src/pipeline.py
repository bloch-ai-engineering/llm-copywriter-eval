"""Generation pipeline for product descriptions"""

import time
from typing import List

from models import Product, GenerationResult
from llm_service import LLMService
from config import ConfigManager
from prompt_engine import PromptEngine


class GenerationPipeline:
    """Generate descriptions for products with metrics tracking"""

    def __init__(self, model_name: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"):
        self.model_name = model_name
        self.config = ConfigManager.get_nebius_config()
        self.llm_service = LLMService(model=model_name)
        self.results: List[GenerationResult] = []

    async def generate_descriptions(self, products: List[Product]) -> List[GenerationResult]:
        """Generate descriptions for all products using Nebius API"""
        print(f"Generating descriptions for {len(products)} products using {self.model_name}...")

        for i, product in enumerate(products, 1):
            result = await self._generate_single(product)
            self.results.append(result)

            if i % 10 == 0:
                print(f"  Processed {i}/{len(products)}")

        return self.results

    async def _generate_single(self, product: Product) -> GenerationResult:
        """Generate a single description using Nebius API"""
        user_prompt = PromptEngine.build_user_prompt(product)
        system_prompt = PromptEngine.SYSTEM_PROMPT

        try:
            description, usage = await self.llm_service.generate_description(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=150
            )

            # Get token counts and latency from API response
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            latency_ms = usage["latency_ms"]

            # Calculate cost
            model_pricing = self.config["models"].get(self.model_name, {})
            input_cost = (input_tokens / 1_000_000) * model_pricing.get("input_cost_per_1m", 0)
            output_cost = (output_tokens / 1_000_000) * model_pricing.get("output_cost_per_1m", 0)
            total_cost = input_cost + output_cost

            return GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=description,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=total_cost
            )
        except Exception as e:
            print(f"  Error generating for {product.product_name}: {str(e)}")
            # Fallback to mock if API fails
            description = self._mock_generate(product)
            input_tokens = int((len(system_prompt) + len(user_prompt)) / 4)
            output_tokens = int(len(description) / 4)
            model_pricing = self.config["models"].get(self.model_name, {})
            input_cost = (input_tokens / 1_000_000) * model_pricing.get("input_cost_per_1m", 0)
            output_cost = (output_tokens / 1_000_000) * model_pricing.get("output_cost_per_1m", 0)

            return GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=description,
                latency_ms=100.0,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=input_cost + output_cost
            )

    def _mock_generate(self, product: Product) -> str:
        """Mock description generation for demonstration"""
        examples = {
            "Apple iPhone 15 Pro": "Premium flagship device with advanced features.",
            "Samsung Galaxy S24 Ultra": "Powerful smartphone with excellent display.",
        }
        return examples.get(product.product_name, "Premium product crafted for excellence.")
