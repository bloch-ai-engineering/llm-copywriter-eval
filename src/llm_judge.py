"""
Task 5: LLM-as-a-Judge
Evaluates generated product descriptions using Qwen3-30B-A3B-Instruct-2507 via Nebius.
Reads results/llm_judge.xlsx, fills evaluation columns, and saves results.
"""

import argparse
import os
import asyncio
import time
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

JUDGE_MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"
DEFAULT_FILE = "results/llm_judge.xlsx"

Verdict = Literal["good", "ok", "bad"]


# ---------- Pydantic schemas (explanation before verdict) ----------

class CriterionEval(BaseModel):
    explanation: str
    verdict: Verdict


class DescriptionEvaluation(BaseModel):
    fluency: CriterionEval
    grammar: CriterionEval
    tone: CriterionEval
    length: CriterionEval
    grounding: CriterionEval


# ---------- Nebius client ----------

def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("NEBIUS_API_KEY"),
        base_url="https://api.tokenfactory.nebius.com/v1/",
    )


# ---------- Judge prompts ----------

SYSTEM_PROMPT_ALL = """\
You are a strict but fair e-commerce content evaluator.
You will be given a product's structured data and an AI-generated product description.
Evaluate the description on five criteria using the rubric below.

Rubric:

Criterion | Good | Ok | Bad
Fluency   | Sentences flow naturally; transitions are smooth; easily readable; no awkward phrasing. | Some minor awkward phrasing or slightly unnatural sentence order; meaning still clear. | Frequent awkward phrasing; choppy or disjointed sentences; hard to read.
Grammar   | No spelling, punctuation, or capitalization errors. | 1–2 minor errors per ~100 words; does not impede understanding. | Frequent spelling or punctuation errors; grammar issues interfere with comprehension.
Tone      | Professional yet approachable, persuasive without being pushy, conveys value | Mostly professional but occasionally missing warmth or conviction | Sterile/robotic, overly aggressive, or mismatched to e-commerce context
Length    | 50–90 words. | 40–49 or 91–110 words. | <40 or >110 words.
Grounding | All statements supported by provided information; no hallucinations or assumptions. | Mostly accurate; minor unsupported statements that do not change meaning. | Frequent unsupported claims; contradicts or invents information.

For each criterion output an explanation (your reasoning) FIRST, then a verdict of "good", "ok", or "bad".\
"""

CRITERION_RUBRICS = {
    "fluency":   "Fluency: Are sentences natural and easy to read? Good: Flows naturally; no awkward phrasing. Ok: Some minor awkwardness; meaning still clear. Bad: Choppy or disjointed; hard to read.",
    "grammar":   "Grammar: Is spelling and punctuation correct? Good: No errors. Ok: 1–2 minor errors; does not impede understanding. Bad: Frequent errors; interfere with comprehension.",
    "tone":      "Tone: Does it match a friendly, credible sales voice? Good: Professional yet approachable, persuasive without being pushy. Ok: Mostly professional but occasionally missing warmth. Bad: Sterile/robotic, overly aggressive, or mismatched to e-commerce context.",
    "length":    "Length: Is the description the right length? Good: 50–90 words. Ok: 40–49 or 91–110 words. Bad: <40 or >110 words.",
    "grounding": "Grounding: Does it stick only to provided product information? Good: All statements supported; no hallucinations. Ok: Mostly accurate; minor unsupported statements. Bad: Frequent unsupported claims or invented information.",
}


def build_user_prompt(product_name: str, attributes: str, material: str, warranty: str, description: str) -> str:
    word_count = len(description.split())
    return f"""\
Product information:
- Name: {product_name}
- Attributes: {attributes}
- Material: {material}
- Warranty: {warranty}

Generated description ({word_count} words):
\"\"\"{description}\"\"\"

Evaluate the description according to the rubric. Return valid JSON matching this schema:
{{
  "fluency":   {{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}},
  "grammar":   {{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}},
  "tone":      {{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}},
  "length":    {{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}},
  "grounding": {{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}}
}}\
"""


def build_criterion_prompt(criterion: str, product_name: str, attributes: str, material: str, warranty: str, description: str) -> str:
    word_count = len(description.split())
    product_block = f"""\
Product information:
- Name: {product_name}
- Attributes: {attributes}
- Material: {material}
- Warranty: {warranty}

""" if criterion == "grounding" else ""
    return f"""\
{product_block}Generated description ({word_count} words):
\"\"\"{description}\"\"\"

Evaluate ONLY the following criterion:
{CRITERION_RUBRICS[criterion]}

Output your reasoning FIRST, then your verdict. Return valid JSON:
{{"explanation": "<reasoning>", "verdict": "<good|ok|bad>"}}\
"""


# ---------- Core judge functions ----------

async def _call_llm(client: AsyncOpenAI, system: str, user: str, max_tokens: int, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries - 1:
                print(f"    Attempt {attempt + 1} failed: {e}. Retrying…")
                await asyncio.sleep(2)
            else:
                raise


async def judge_description(
    client: AsyncOpenAI,
    product_name: str,
    attributes: str,
    material: str,
    warranty: str,
    description: str,
) -> DescriptionEvaluation:
    """Evaluate all criteria in a single API call."""
    user_prompt = build_user_prompt(product_name, attributes, material, warranty, description)
    raw = await _call_llm(client, SYSTEM_PROMPT_ALL, user_prompt, max_tokens=1200)
    return DescriptionEvaluation.model_validate_json(raw)


async def judge_description_per_criterion(
    client: AsyncOpenAI,
    product_name: str,
    attributes: str,
    material: str,
    warranty: str,
    description: str,
    criterion_order: list[str],
) -> DescriptionEvaluation:
    """Evaluate each criterion in a separate API call (all in parallel)."""
    system = "You are a strict but fair e-commerce content evaluator."

    async def _eval_one(criterion: str) -> tuple[str, CriterionEval]:
        user_prompt = build_criterion_prompt(criterion, product_name, attributes, material, warranty, description)
        raw = await _call_llm(client, system, user_prompt, max_tokens=300)
        return criterion, CriterionEval.model_validate_json(raw)

    pairs = await asyncio.gather(*(_eval_one(c) for c in criterion_order))
    return DescriptionEvaluation(**dict(pairs))


# ---------- Main pipeline ----------

async def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge for product descriptions")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Path to the xlsx file to evaluate (default: %(default)s)")
    parser.add_argument("--per-criterion", action="store_true", help="Evaluate each criterion in a separate API call instead of all at once")
    args = parser.parse_args()

    input_file = args.file
    output_file = args.file

    print(f"Loading {input_file}…")
    df = pd.read_excel(input_file)

    client = get_client()

    # Columns to fill (match the xlsx header names)
    eval_columns = {
        "fluency":    ("fluency",    "explanation"),   # (verdict col, explanation col)
        "grammar":    ("grammar",    "explanation"),
        "tone":       ("tone",       "explanation"),
        "length":     ("length",     "explanation"),
        "grounding":  ("grounding",  "explanation"),
    }

    # Pandas auto-renames duplicate headers: explanation, explanation.1, …
    # Re-map all of them to <criterion>_explanation for unambiguous access.
    criterion_order = ["fluency", "grammar", "tone", "length", "grounding"]
    exp_idx = 0
    renamed = []
    for col in df.columns:
        col_str = str(col) if col is not None else ""
        if col_str == "explanation" or col_str.startswith("explanation."):
            renamed.append(f"{criterion_order[exp_idx]}_explanation")
            exp_idx += 1
        else:
            renamed.append(col_str if col_str else f"_unnamed_{len(renamed)}")
    df.columns = renamed

    # Cast all evaluation columns to object so pandas accepts string values
    for criterion in criterion_order:
        df[criterion] = df[criterion].astype(object)
        df[f"{criterion}_explanation"] = df[f"{criterion}_explanation"].astype(object)

    total = len(df)
    sem = asyncio.Semaphore(10)  # max 10 concurrent API calls

    async def process_row(idx, row) -> None:
        product_name = str(row.get("product_name", ""))
        attributes   = str(row.get("product_attributes", ""))
        material     = str(row.get("material", ""))
        warranty     = str(row.get("warranty", ""))
        description  = str(row.get("generated_description", ""))

        if not description or description in ("nan", "None", ""):
            print(f"[{idx + 1}/{total}] Skipping row {idx} — no description.")
            return

        print(f"[{idx + 1}/{total}] Judging: {product_name[:50]}…")
        t0 = time.time()

        async with sem:
            try:
                if args.per_criterion:
                    evaluation = await judge_description_per_criterion(
                        client, product_name, attributes, material, warranty, description, criterion_order
                    )
                else:
                    evaluation = await judge_description(
                        client, product_name, attributes, material, warranty, description
                    )
            except Exception as e:
                print(f"    [{idx + 1}/{total}] ERROR: {e}")
                return

        elapsed = time.time() - t0

        for criterion in criterion_order:
            crit_eval: CriterionEval = getattr(evaluation, criterion)
            df.at[idx, criterion]                  = crit_eval.verdict
            df.at[idx, f"{criterion}_explanation"] = crit_eval.explanation

        print(
            f"    [{idx + 1}/{total}] fluency={evaluation.fluency.verdict}  grammar={evaluation.grammar.verdict}  "
            f"tone={evaluation.tone.verdict}  length={evaluation.length.verdict}  "
            f"grounding={evaluation.grounding.verdict}  ({elapsed:.1f}s)"
        )

    await asyncio.gather(*(process_row(idx, row) for idx, row in df.iterrows()))

    # Restore original column names before saving (rename back explanation columns)
    restore_map = {f"{c}_explanation": "explanation" for c in criterion_order}
    df.rename(columns=restore_map, inplace=True)

    print(f"\nSaving results to {output_file}…")
    df.to_excel(output_file, index=False)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
