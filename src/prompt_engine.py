"""Prompt engineering for generation and evaluation"""

from models import Product


class PromptEngine:
    """Craft system and user prompts to guide generation"""

    SYSTEM_PROMPT = """You are an expert e-commerce product description writer.
 Your task is to craft persuasive, compelling product descriptions that engage customers and drive sales.
REQUIREMENTS:
Length: Exactly 50–90 words.
Tone: Friendly, professional, and approachable, highlighting genuine value.
Grounding: Use only the information provided; do not invent features or specs.
Grammar: Perfect spelling, punctuation, and capitalization.
Flow: Sentences should read naturally, with smooth transitions and logical pacing.
APPROACH:
Identify the key selling points from the provided product attributes.
Lead with the most compelling feature or use case.
Use specific product details to support quality and value.
Highlight material, craftsmanship, or warranty as trust signals.
Close with a clear value statement.
AVOID:
Unsupported superlatives (e.g., “the best” without context).
Unverified claims about performance or durability.
Generic or vague language that could describe any product.
Generate only the product description.
"""

    @staticmethod
    def build_user_prompt(product: Product) -> str:
        """Build user prompt with product data"""
        return f"""Product Name: {product.product_name}
Features & Attributes: {product.attributes}
Materials: {product.material}
Warranty: {product.warranty}

Write a compelling 50-90 word description that will convince a customer to buy this product."""

    @staticmethod
    def build_judge_prompt(product: Product, description: str) -> str:
        """Judge prompt with rubric definitions for grounding evaluation"""
        return f"""You are an expert evaluator of e-commerce product descriptions.

ORIGINAL PRODUCT DATA:
- Product Name: {product.product_name}
- Features & Attributes: {product.attributes}
- Materials: {product.material}
- Warranty: {product.warranty}

DESCRIPTION TO EVALUATE:
{description}

EVALUATION CRITERIA (evaluate each separately):

1. FLUENCY: Are sentences natural and easy to read?
   - Good: Flows naturally with varied sentence structure, no awkward phrasing
   - Ok: Generally readable but may have minor awkwardness
   - Bad: Choppy, hard to read, or unnatural phrasing

2. GRAMMAR: Is spelling and punctuation correct?
   - Good: No errors, correct punctuation throughout
   - Ok: 1-2 minor errors that don't impede understanding
   - Bad: 3+ errors OR errors that impede understanding

3. TONE: Does it match a friendly, credible sales voice?
   - Good: Professional yet approachable, persuasive without being pushy
   - Ok: Mostly professional but occasionally missing warmth
   - Bad: Sterile/robotic, overly aggressive, or mismatched

4. GROUNDING: Does it stick ONLY to provided product information?
   - Good: Uses only facts from attributes/materials/warranty, no hallucinations
   - Ok: Mostly grounded with 1 minor inference
   - Bad: Contains made-up features or unverified claims

Evaluate each criterion independently and provide reasoning before your verdict."""

    @staticmethod
    def _build_criterion_prompt(criterion: str, product: Product, description: str) -> str:
        """Build isolated criterion evaluation prompt"""
        criterion_definitions = {
            'fluency': "Are sentences natural and easy to read? Good: Flows naturally with varied sentence structure. Ok: Generally readable but may have minor awkwardness. Bad: Choppy, hard to read.",
            'grammar': "Is spelling and punctuation correct? Good: No errors. Ok: 1-2 minor errors. Bad: 3+ errors.",
            'tone': "Does it match a friendly, credible sales voice? Good: Professional yet approachable. Ok: Mostly professional. Bad: Sterile/robotic or overly aggressive.",
            'grounding': "Does it stick ONLY to provided information? Good: Uses only facts, no hallucinations. Ok: Mostly grounded with 1 minor inference. Bad: Contains made-up features."
        }

        return f"""Evaluate ONLY the {criterion.upper()} criterion for this product description.

PRODUCT DATA:
- Name: {product.product_name}
- Attributes: {product.attributes}
- Materials: {product.material}
- Warranty: {product.warranty}

DESCRIPTION:
{description}

CRITERION: {criterion_definitions.get(criterion, 'Unknown criterion')}

Provide your reasoning before your verdict. Answer with explanation and verdict."""
