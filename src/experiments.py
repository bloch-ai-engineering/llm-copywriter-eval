"""Improvement experiments framework"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Experiment:
    """Improvement experiment design"""
    name: str
    description: str
    changes: Dict
    baseline_pass_rate: float = 0.0
    improved_pass_rate: float = 0.0
    improvement: float = 0.0


class ImprovementExperiment:
    """Design and track improvement experiments"""

    @staticmethod
    def design_experiments() -> List[Experiment]:
        """Design improvement experiments"""
        return [
            Experiment(
                name="Experiment 1: Enhanced Prompt Engineering",
                description="Add specific constraints and examples to system prompt",
                changes={
                    "prompt_enhancement": "Add bullet-point format constraints",
                    "specific_examples": "Include good/bad examples"
                }
            ),
            Experiment(
                name="Experiment 2: Model Upgrade",
                description="Switch to larger model for better quality",
                changes={
                    "model": "meta-llama/Llama-3.3-70B-Instruct",
                    "rationale": "Larger model should handle complex criteria better"
                }
            ),
            Experiment(
                name="Experiment 3: Temperature Tuning",
                description="Reduce temperature for more factual, grounded outputs",
                changes={
                    "temperature": 0.3,
                    "top_p": 0.7,
                    "rationale": "Lower temperature reduces hallucinations, improves grounding"
                }
            ),
        ]
