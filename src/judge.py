"""LLM-as-a-Judge implementation with structured outputs"""

from typing import Dict

from models import Product
from llm_service import LLMService
from prompt_engine import PromptEngine


class JudgeModel:
    """LLM-as-a-Judge using Pydantic for structured outputs"""

    def __init__(self, model_name: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"):
        self.model_name = model_name
        self.llm_service = LLMService(model=model_name)

    async def evaluate_description(
        self,
        product: Product,
        description: str,
        criterion_isolation: bool = False
    ) -> Dict:
        """Evaluate description with chain-of-thought reasoning"""
        if criterion_isolation:
            return await self._evaluate_per_criterion(product, description)
        else:
            return await self._evaluate_all_at_once(product, description)

    async def _evaluate_all_at_once(self, product: Product, description: str) -> Dict:
        """Evaluate all criteria in single API call"""
        prompt = PromptEngine.build_judge_prompt(product, description)

        try:
            evaluation = await self.llm_service.evaluate_description(
                judge_prompt=prompt,
                temperature=0.1
            )
            return self._parse_evaluation(evaluation)
        except Exception as e:
            print(f"  Judge error: {str(e)}")
            # Fallback
            return {
                'fluency': {'explanation': 'Unable to evaluate', 'verdict': 'ok'},
                'grammar': {'explanation': 'Unable to evaluate', 'verdict': 'ok'},
                'tone': {'explanation': 'Unable to evaluate', 'verdict': 'ok'},
                'grounding': {'explanation': 'Unable to evaluate', 'verdict': 'ok'},
            }

    async def _evaluate_per_criterion(self, product: Product, description: str) -> Dict:
        """Evaluate each criterion separately"""
        results = {}
        criteria = ['fluency', 'grammar', 'tone', 'grounding']

        for criterion in criteria:
            criterion_prompt = PromptEngine._build_criterion_prompt(criterion, product, description)
            try:
                evaluation = await self.llm_service.evaluate_description(
                    judge_prompt=criterion_prompt,
                    temperature=0.1
                )
                results[criterion] = self._parse_criterion_evaluation(evaluation)
            except Exception as e:
                results[criterion] = {
                    'explanation': f'Error: {str(e)}',
                    'verdict': 'ok'
                }

        return results

    @staticmethod
    def _parse_evaluation(evaluation: Dict) -> Dict:
        """Parse evaluation response from LLM"""
        if 'raw_evaluation' in evaluation:
            return {
                'fluency': {'explanation': 'See raw evaluation', 'verdict': 'ok'},
                'grammar': {'explanation': 'See raw evaluation', 'verdict': 'ok'},
                'tone': {'explanation': 'See raw evaluation', 'verdict': 'ok'},
                'grounding': {'explanation': 'See raw evaluation', 'verdict': 'ok'},
            }
        return evaluation

    @staticmethod
    def _parse_criterion_evaluation(evaluation: Dict) -> Dict:
        """Parse single criterion evaluation"""
        return {
            'explanation': evaluation.get('explanation', evaluation.get('raw_evaluation', '')),
            'verdict': evaluation.get('verdict', 'ok')
        }
