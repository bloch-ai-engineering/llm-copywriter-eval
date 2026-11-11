"""Data models and structures"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Optional


@dataclass
class Product:
    """Product from dataset"""
    product_name: str
    attributes: str
    material: str
    warranty: str


@dataclass
class GenerationResult:
    """Result from a single generation call"""
    product_name: str
    product_attributes: str
    material: str
    warranty: str
    generated_description: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float = 0.0
    # Rubric criteria ratings (filled by evaluators)
    fluency: Optional[str] = None
    grammar: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    grounding: Optional[str] = None
    latency: Optional[str] = None
    cost: Optional[str] = None
    final_score: Optional[str] = None  # "pass" or "fail"

    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame"""
        return asdict(self)
