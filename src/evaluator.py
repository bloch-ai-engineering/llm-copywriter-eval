"""Manual evaluation of generated descriptions"""

import re
from typing import List, Dict

from models import GenerationResult
from evaluation_framework import Rating, EvaluationRubric, PassFailDefinition


class ManualEvaluator:
    """Manual (Human) evaluation of product descriptions"""

    @staticmethod
    def evaluate_sample(results: List[GenerationResult], sample_size: int = 12) -> Dict:
        """Manually evaluate a sample of products"""
        print(f"Evaluating {sample_size} products...")

        sample_indices = list(range(0, min(sample_size, len(results))))
        evaluations = {}

        for idx in sample_indices:
            result = results[idx]
            evaluation = ManualEvaluator._score_description(result)
            evaluations[result.product_name] = evaluation

            # Update result with ratings
            for criterion, rating in evaluation['ratings'].items():
                setattr(result, criterion.lower(), rating)

            # Compute final score
            result.final_score = "pass" if evaluation['passes'] else "fail"

        return evaluations

    @staticmethod
    def _score_description(result: GenerationResult) -> Dict:
        """Score a single description against rubric"""
        description = result.generated_description
        ratings = {}

        # Length evaluation (objective)
        ratings['length'] = EvaluationRubric.evaluate_length(description)

        # Latency evaluation (objective)
        ratings['latency'] = EvaluationRubric.evaluate_latency(result.latency_ms)

        # Cost evaluation (objective)
        ratings['cost'] = EvaluationRubric.evaluate_cost(result.cost_usd)

        # Subjective evaluations
        ratings['fluency'] = Rating(ManualEvaluator._evaluate_fluency(description))
        ratings['grammar'] = Rating(ManualEvaluator._evaluate_grammar(description))
        ratings['tone'] = Rating(ManualEvaluator._evaluate_tone(description))
        ratings['grounding'] = Rating(ManualEvaluator._evaluate_grounding(
            description, result.product_attributes
        ))

        # Apply pass/fail rules
        passes = PassFailDefinition.compute_final_score(ratings)

        return {
            'ratings': {k: v.value for k, v in ratings.items()},
            'passes': passes
        }

    @staticmethod
    def _evaluate_fluency(text: str) -> str:
        """Evaluate fluency"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) >= 3 and all(len(s.split()) > 5 for s in sentences):
            return "good"
        elif len(sentences) >= 2:
            return "ok"
        return "bad"

    @staticmethod
    def _evaluate_grammar(text: str) -> str:
        """Evaluate grammar"""
        error_patterns = [r'\s{2,}', r'\b[A-Z]{2,}\b']
        error_count = sum(len(re.findall(p, text)) for p in error_patterns)
        if error_count == 0:
            return "good"
        elif error_count <= 2:
            return "ok"
        return "bad"

    @staticmethod
    def _evaluate_tone(text: str) -> str:
        """Evaluate tone"""
        sales_words = ['premium', 'exceptional', 'stunning', 'delivers', 'perfection', 'powerful']
        match_count = sum(1 for word in sales_words if word.lower() in text.lower())
        if match_count >= 3:
            return "good"
        elif match_count >= 1:
            return "ok"
        return "bad"

    @staticmethod
    def _evaluate_grounding(description: str, attributes: str) -> str:
        """Evaluate grounding"""
        attr_words = set(attributes.lower().split())
        desc_words = set(description.lower().split())
        overlap = len(attr_words & desc_words)
        if overlap >= 8:
            return "good"
        elif overlap >= 4:
            return "ok"
        return "bad"
