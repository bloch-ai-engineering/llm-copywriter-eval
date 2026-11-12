# LLM Copywriter Eval

**Generate e-commerce product descriptions with an LLM, evaluate them with a human rubric and an LLM-as-a-judge, and measure how far the two agree.**

![Python](https://img.shields.io/badge/python-3.11+-blue) ![OpenAI SDK](https://img.shields.io/badge/OpenAI%20SDK-Nebius%20Token%20Factory-black) ![Pydantic](https://img.shields.io/badge/Pydantic-structured%20outputs-e92063) ![pandas](https://img.shields.io/badge/pandas-xlsx-150458)

**Notebooks**: for the best reading experience, open them in nbviewer (full-page rendering) or Colab:

| Notebook | Read | Run |
|---|---|---|
| `product_description_eval.ipynb` | [![nbviewer](https://img.shields.io/badge/view-nbviewer-orange?logo=jupyter)](https://nbviewer.org/github/bloch-ai-engineering/llm-copywriter-eval/blob/main/notebooks/product_description_eval.ipynb) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bloch-ai-engineering/llm-copywriter-eval/blob/main/notebooks/product_description_eval.ipynb) |


## The problem

An online store wants to auto-write product descriptions for 50 products. Before shipping, you need to know if the copy is any good. That means a rubric, a baseline, a way to improve it, and a way to evaluate it at scale without a human reading every line.

## What we built

| Step | What it does |
|---|---|
| **1. Rubric** | 7 criteria (Fluency, Grammar, Tone, Length, Grounding, Latency, Cost), each rated Good / Ok / Bad. **Pass** = ≥4 Good and no Bad. **Go / no-go**: Grounding and Grammar must be Good. |
| **2. Generation** | Async, rate-limited generation with `Meta-Llama-3.1-8B-Instruct` via Nebius Token Factory. Latency and token cost are tracked per call. |
| **3. Human eval** | Manual rating of a 12-product sample against the rubric. |
| **4. Improvement cycle** | 3 experiments: baseline, a stricter prompt at T=0.5, and a larger model (`Qwen3-30B-A3B`). |
| **5. LLM-as-a-judge** | `Qwen3-30B-A3B-Instruct-2507` grades every description with Pydantic structured output, *explanation before verdict*. Runs in two modes: all criteria at once, and criterion-by-criterion. |
| **6. Judge vs. human** | Per-criterion agreement analysis and a recommendation. |

```
products.csv ──► PromptEngine ──► LLMService (async, cost/latency) ──► descriptions.xlsx
                                                                          │
                       human rubric ratings ◄─────────────────────────────┤
                       LLM judge (Pydantic schema, per-criterion) ◄───────┘
                                       │
                                       ▼
                            agreement analysis (Task 6)
```

## Results

**Improvement cycle (12-product sample):**

| Experiment | Avg latency | Avg cost / call | Pass rate |
|---|---|---|---|
| Baseline: Llama-3.1-8B, T=0.7 | 3,207 ms | $0.000011 | 100% |
| Stricter prompt, T=0.5 | 3,456 ms | $0.000010 | 100% (tighter word counts) |
| Qwen3-30B + stricter prompt | **2,413 ms** | $0.000028 | 100% |

**LLM judge on all 50 products:** 96% pass. Failures are mostly on grounding.

**Agreement between the judge and human raters:**

| Criterion | Agreement |
|---|---|
| Length | 100% |
| Grounding | 100% |
| Grammar | 92% |
| Tone | 33% |
| Fluency | 25% |

The judge agrees on objective criteria and is too lenient on subjective ones: it rated everything "good", while humans gave "ok". Judging criterion-by-criterion didn't change agreement. The takeaway: calibrate a judge against a human-labelled subset before trusting it on tone and fluency.

Full write-up: [`notebooks/product_description_eval.ipynb`](notebooks/product_description_eval.ipynb) and [`docs/report.md`](docs/report.md).

## Project structure

```
├── notebooks/product_description_eval.ipynb   # final submission: all 6 tasks, outputs included
├── src/
│   ├── main.py                     # end-to-end pipeline (tasks 1–4)
│   ├── evaluation_framework.py     # rubric + pass/fail rules
│   ├── llm_service.py              # async Nebius client with cost & latency tracking
│   ├── prompt_engine.py            # generation prompts
│   ├── pipeline.py                 # concurrent generation
│   ├── evaluator.py                # rule-based scoring (length, latency, cost)
│   ├── improvement_experiments.py  # task 4 experiments
│   ├── llm_judge.py                # task 5 LLM-as-a-judge CLI
│   └── ...
├── data/products.csv               # 50 products
├── results/                        # generations, human ratings, judge ratings, experiment results
└── docs/
    ├── assignment/                 # original assignment brief
    ├── report.md                   # written answers
    └── pricing.md                  # model pricing reference
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # add your NEBIUS_API_KEY

python src/main.py                                   # generate + evaluate + experiments
python src/llm_judge.py --file results/llm_judge.xlsx  # LLM-as-a-judge
```

Run commands from the repo root.

## Context

This was an assignment for **Nebius Academy: AI Performance Engineering** (module "From AI Model to AI Agent"). The original brief is in [`docs/assignment/`](docs/assignment/).

## Authors

**Nathanael Bloch** · **Tomer Porat**
