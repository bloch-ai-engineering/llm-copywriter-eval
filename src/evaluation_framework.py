"""
LLM Evaluation Framework for Product Descriptions
Implements rigorous rubric definition and evaluation logic
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
import re


class Rating(str, Enum):
    """Three-level evaluation scale"""
    GOOD = "good"
    OK = "ok"
    BAD = "bad"


@dataclass
class RubricCriterion:
    """Definition of a single evaluation criterion with clear thresholds"""
    name: str
    description: str
    good_definition: str
    ok_definition: str
    bad_definition: str

    def evaluate(self, criterion_name: str, text: str, product_data: Optional[Dict] = None) -> Rating:
        """
        Evaluate text against this criterion.
        Must be called from specific criterion evaluators below.
        """
        raise NotImplementedError("Use specific criterion evaluators")


class EvaluationRubric:
    """
    TASK 1: Define Evaluation Rubric

    Clear, objective criteria for rating product descriptions.
    Each criterion has explicit definitions to minimize subjectivity.
    """

    FLUENCY = RubricCriterion(
        name="Fluency",
        description="Natural, easy-to-read sentences",
        good_definition="Flows naturally with varied sentence structure, no awkward phrasing",
        ok_definition="Generally readable but may have minor awkwardness or repetitive structure",
        bad_definition="Choppy, hard to read, unclear flow, or unnatural phrasing"
    )

    GRAMMAR = RubricCriterion(
        name="Grammar",
        description="Correct spelling & punctuation",
        good_definition="No spelling errors, correct punctuation throughout",
        ok_definition="1-2 minor spelling/punctuation errors that don't impede understanding",
        bad_definition="3+ errors OR errors that impede understanding"
    )

    TONE = RubricCriterion(
        name="Tone",
        description="Matches friendly, credible sales voice",
        good_definition="Professional yet approachable, persuasive without being pushy, conveys value",
        ok_definition="Mostly professional but occasionally missing warmth or conviction",
        bad_definition="Sterile/robotic, overly aggressive, or mismatched to e-commerce context"
    )

    LENGTH = RubricCriterion(
        name="Length",
        description="50-90 word target",
        good_definition="50-90 words (within target range)",
        ok_definition="40-49 or 91-110 words (acceptable deviation)",
        bad_definition="<40 or >110 words (outside acceptable range)"
    )

    GROUNDING = RubricCriterion(
        name="Grounding",
        description="Sticks to information provided",
        good_definition="Uses only facts from product attributes, materials, warranty. No hallucinations.",
        ok_definition="Mostly grounded with 1 minor inference (e.g., 'compact design' from dimensions)",
        bad_definition="Contains made-up features, unverified claims, or fabricated specifications"
    )

    LATENCY = RubricCriterion(
        name="Latency",
        description="Time to first byte / full response",
        good_definition="<2000ms average latency (reasonable for real-time use)",
        ok_definition="2000-5000ms latency (acceptable for batch)",
        bad_definition=">5000ms latency (problematic for latency-sensitive apps)"
    )

    COST = RubricCriterion(
        name="Cost",
        description="Relative inference or API cost per 1K tokens",
        good_definition="<$0.0002 per 1K tokens (cost-effective)",
        ok_definition="$0.0002-0.0005 per 1K tokens (moderate cost)",
        bad_definition=">$0.0005 per 1K tokens (expensive)"
    )

    @staticmethod
    def evaluate_length(text: str) -> Rating:
        """Evaluate word count against 50-90 word target"""
        word_count = len(text.split())
        if 50 <= word_count <= 90:
            return Rating.GOOD
        elif 40 <= word_count <= 110:
            return Rating.OK
        else:
            return Rating.BAD

    @staticmethod
    def evaluate_latency(latency_ms: float) -> Rating:
        """Evaluate latency in milliseconds"""
        if latency_ms < 2000:
            return Rating.GOOD
        elif latency_ms <= 5000:
            return Rating.OK
        else:
            return Rating.BAD

    @staticmethod
    def evaluate_cost(cost_usd: float) -> Rating:
        """Evaluate cost per 1K tokens"""
        if cost_usd < 0.0002:
            return Rating.GOOD
        elif cost_usd <= 0.0005:
            return Rating.OK
        else:
            return Rating.BAD


class PassFailDefinition:
    """
    TASK 1: Define Pass/Fail Rules

    Three-part framework:
    1. Mandatory go/no-go gates (automatic failure conditions)
    2. Cumulative good criteria minimum
    3. Maximum acceptable bad/ok criteria
    """

    # Cumulative pass bar: at least 5 criteria rated "good"
    MIN_GOOD_CRITERIA = 5

    # Maximum acceptable bad criteria
    MAX_BAD_CRITERIA = 1

    # Maximum acceptable ok criteria (affects overall quality)
    MAX_OK_CRITERIA = 2

    # Go/no-go rules: single criteria that trigger automatic failure
    MANDATORY_CRITERIA = {
        "Grounding": "bad"  # If grounding is bad, description fails immediately
    }

    @staticmethod
    def compute_final_score(ratings: Dict[str, Rating]) -> bool:
        """
        Compute pass/fail based on comprehensive rubric rules.

        Returns True (pass) if:
        1. No mandatory criteria trigger automatic failure
        2. At least MIN_GOOD_CRITERIA are "good"
        3. No more than MAX_BAD_CRITERIA are "bad"
        4. No more than MAX_OK_CRITERIA are "ok"

        Rationale:
        - "Ok" ratings indicate mediocre criteria that lower overall quality
        - Too many "ok" ratings = inconsistent, unreliable output
        - Limit "ok" to 2 max to ensure mostly good/acceptable performance
        """
        # Check mandatory go/no-go rules FIRST
        for criterion, required_rating in PassFailDefinition.MANDATORY_CRITERIA.items():
            if ratings.get(criterion) == Rating(required_rating):
                print(f"  ✗ Mandatory failure: {criterion} = {required_rating}")
                return False

        # Count ratings
        good_count = sum(1 for r in ratings.values() if r == Rating.GOOD)
        ok_count = sum(1 for r in ratings.values() if r == Rating.OK)
        bad_count = sum(1 for r in ratings.values() if r == Rating.BAD)

        # Apply pass rules
        passes_good = good_count >= PassFailDefinition.MIN_GOOD_CRITERIA
        passes_bad = bad_count <= PassFailDefinition.MAX_BAD_CRITERIA
        passes_ok = ok_count <= PassFailDefinition.MAX_OK_CRITERIA

        # Debug output
        if not passes_good:
            print(f"  ✗ Insufficient good criteria: {good_count}/{PassFailDefinition.MIN_GOOD_CRITERIA}")
        if not passes_bad:
            print(f"  ✗ Too many bad criteria: {bad_count} (max {PassFailDefinition.MAX_BAD_CRITERIA})")
        if not passes_ok:
            print(f"  ✗ Too many ok criteria: {ok_count} (max {PassFailDefinition.MAX_OK_CRITERIA})")

        return passes_good and passes_bad and passes_ok


# Export for use in other modules
RUBRIC_CRITERIA = [
    EvaluationRubric.FLUENCY,
    EvaluationRubric.GRAMMAR,
    EvaluationRubric.TONE,
    EvaluationRubric.LENGTH,
    EvaluationRubric.GROUNDING,
    EvaluationRubric.LATENCY,
    EvaluationRubric.COST,
]

CRITERION_NAMES = [c.name for c in RUBRIC_CRITERIA]
