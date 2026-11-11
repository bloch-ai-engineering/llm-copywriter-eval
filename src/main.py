"""Main execution pipeline for LLM Evaluation System"""

import asyncio
from data_loader import DataLoader
from pipeline import GenerationPipeline
from evaluator import ManualEvaluator
from experiments import ImprovementExperiment
from judge import JudgeModel
from exporter import ExcelExporter
from evaluation_framework import CRITERION_NAMES, PassFailDefinition


async def main():
    """Main execution pipeline"""
    print("=" * 70)
    print("LLM EVALUATION SYSTEM - Tasks 1-6")
    print("=" * 70)

    # Validate connection
    from llm_service import LLMService
    print("\n→ Validating Nebius Token Factory connection...")
    service = LLMService()
    is_valid, error_msg = await service.validate_connection()
    if not is_valid:
        print(f"✗ Connection validation failed: {error_msg}")
        return
    print("✓ Nebius connection validated successfully")

    # TASK 1: Rubric
    print("\n✓ TASK 1: Evaluation Rubric Defined")
    print(f"  Criteria: {', '.join(CRITERION_NAMES)}")
    print(f"  Pass bar: {PassFailDefinition.MIN_GOOD_CRITERIA} good + max {PassFailDefinition.MAX_BAD_CRITERIA} bad")
    print(f"  Go/no-go: Grounding=bad → automatic failure")

    # Load products
    print("\n→ Loading dataset...")
    products = DataLoader.load_csv("data/products.csv")
    print(f"✓ Loaded {len(products)} products")

    # TASK 2: Generate descriptions
    print("\n" + "=" * 70)
    print("TASK 2: Generate Descriptions")
    print("=" * 70)
    pipeline = GenerationPipeline(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct")
    results = await pipeline.generate_descriptions(products)
    print(f"✓ Generated {len(results)} descriptions")

    # TASK 2: Export to Excel
    print("\n→ Exporting to Excel...")
    df = ExcelExporter.export_results(results, "results/generations_with_human_eval.xlsx")
    print(f"✓ Created results/generations_with_human_eval.xlsx ({len(df)} rows, {len(df.columns)} columns)")

    # TASK 3: Manual evaluation
    print("\n" + "=" * 70)
    print("TASK 3: Manual Evaluation")
    print("=" * 70)
    evaluations = ManualEvaluator.evaluate_sample(results, sample_size=12)
    print(f"✓ Evaluated {len(evaluations)} products")

    # Update Excel with evaluations
    for product_name, eval_data in evaluations.items():
        idx = df[df['product_name'] == product_name].index
        if len(idx) > 0:
            i = idx[0]
            for criterion in ['fluency', 'grammar', 'tone', 'length', 'grounding', 'latency', 'cost']:
                df.at[i, criterion] = eval_data['ratings'].get(criterion, 'ok')
            df.at[i, 'final_score'] = 'pass' if eval_data['passes'] else 'fail'
    df.to_excel("results/generations_with_human_eval.xlsx", sheet_name='Results', index=False)

    # Baseline statistics
    pass_count = sum(1 for e in evaluations.values() if e['passes'])
    pass_rate = pass_count / len(evaluations) * 100 if evaluations else 0
    print(f"  Baseline pass rate: {pass_rate:.1f}% ({pass_count}/{len(evaluations)})")

    # Baseline analysis
    print("\n" + "=" * 70)
    print("BASELINE ANALYSIS")
    print("=" * 70)
    criteria = ['fluency', 'grammar', 'tone', 'length', 'grounding']
    criterion_scores = {c: {'good': 0, 'ok': 0, 'bad': 0} for c in criteria}

    for product_name, eval_data in evaluations.items():
        for criterion in criteria:
            rating = eval_data['ratings'].get(criterion, 'ok').lower()
            criterion_scores[criterion][rating] += 1

    print("\nCriteria Performance:")
    for criterion in criteria:
        scores = criterion_scores[criterion]
        good_pct = (scores['good'] / len(evaluations)) * 100 if evaluations else 0
        print(f"  {criterion:12} → Good: {scores['good']:2} ({good_pct:5.1f}%), Ok: {scores['ok']:2}, Bad: {scores['bad']:2}")

    if evaluations:
        best_criterion = max(criteria, key=lambda c: criterion_scores[c]['good'])
        worst_criterion = min(criteria, key=lambda c: criterion_scores[c]['good'])
        print(f"\n  ✓ Best: {best_criterion} ({criterion_scores[best_criterion]['good']} good)")
        print(f"  ✗ Worst: {worst_criterion} ({criterion_scores[worst_criterion]['good']} good)")

    # TASK 4: Improvement experiments
    from improvement_experiments import ExperimentRunner

    runner = ExperimentRunner()
    exp_results = await runner.run_all_experiments(products, sample_size=5)

    # TASK 5-6: Judge model
    # print("\n" + "=" * 70)
    # print("TASK 5-6: LLM-as-a-Judge")
    # print("=" * 70)
    # judge = JudgeModel(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct")
    # print("✓ Judge model initialized")
    # print("  Schema: explanation (string) → verdict (enum: good/ok/bad)")
    # print("  Chain-of-thought: reasoning before verdicts")
    #
    # # Summary
    # print("\n" + "=" * 70)
    # print("SUMMARY")
    # print("=" * 70)
    # print(f"✓ All tasks completed successfully")
    # print(f"  Products processed: {len(results)}")
    # print(f"  Evaluated sample: {len(evaluations)}")
    # print(f"  Baseline pass rate: {pass_rate:.1f}%")
    # print(f"  Output file: assignment_01.xlsx")
    #

if __name__ == "__main__":
    asyncio.run(main())
