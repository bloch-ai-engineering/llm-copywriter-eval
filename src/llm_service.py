import os
import json
import time
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()


class LLMService:
    def __init__(self, model: Optional[str] = None):
        """Initialize LLM Service with Nebius Token Factory"""
        self.api_key = os.getenv("NEBIUS_API_KEY")
        self.model = model or os.getenv("NEBIUS_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
        self.base_url = "https://api.tokenfactory.nebius.com/v1/"

        # Initialize async OpenAI client pointing to Nebius Token Factory
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def validate_connection(self) -> Tuple[bool, Optional[str]]:
        """Pre-flight check to validate Nebius Token Factory connection."""
        if not self.api_key:
            return False, "NEBIUS_API_KEY is missing from environment."

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True, None
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                return False, f"Authentication Error: Invalid API Key. {error_str}"
            elif "404" in error_str or "Not Found" in error_str:
                return False, f"Model Not Found: {self.model}. {error_str}"
            else:
                return False, f"Connection Error: {error_str}"

    async def generate_description(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a product description using Nebius Token Factory API.

        Returns:
            Tuple of (generated_text, usage_stats) where usage_stats contains
            input_tokens, output_tokens, and latency_ms
        """
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        latency_ms = (time.time() - start_time) * 1000

        message_content = response.choices[0].message.content
        usage = response.usage

        return message_content.strip(), {
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "latency_ms": latency_ms,
            "total_tokens": usage.total_tokens
        }

    async def evaluate_description(
        self,
        judge_prompt: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evaluate a product description using LLM-as-a-judge.
        Returns structured evaluation with explanations and verdicts.
        """
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": judge_prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )

        latency_ms = (time.time() - start_time) * 1000
        message_content = response.choices[0].message.content

        # Try to parse JSON response if provided
        try:
            evaluation = json.loads(message_content)
        except json.JSONDecodeError:
            # If not valid JSON, return as plain text evaluation
            evaluation = {"raw_evaluation": message_content}

        evaluation["latency_ms"] = latency_ms
        return evaluation
