"""Task 4: Improvement Cycle - Document experiments and results"""

import asyncio
from typing import List, Dict
from models import Product, GenerationResult
from llm_service import LLMService
from prompt_engine import PromptEngine
from evaluator import ManualEvaluator
from config import ConfigManager
import pandas as pd


class ExperimentRunner:
    """Run and document improvement experiments"""

    def __init__(self):
        self.config = ConfigManager.get_nebius_config()
        self.experiments = []

    async def run_all_experiments(self, products: List[Product], sample_size: int = 5) -> Dict:
        """Run all improvement experiments on a sample"""
        sample = products[:sample_size]
        print("\n" + "=" * 70)
        print("TASK 4: IMPROVEMENT CYCLE")
        print("=" * 70)

        # Baseline: 8B model with original prompt
        print("\n→ BASELINE: 8B Model + Original Prompt")
        baseline_results = await self._run_baseline(sample)

        # Experiment 1: Enhanced Prompt Engineering
        print("\n" + "=" * 70)
        print("EXPERIMENT 1: Enhanced Prompt Engineering")
        print("=" * 70)
        exp1_results = await self._experiment_1_prompt_engineering(sample, baseline_results)

        # Experiment 2: Model Upgrade to 70B
        print("\n" + "=" * 70)
        print("EXPERIMENT 2: Model Upgrade (8B → 70B-Instruct)")
        print("=" * 70)
        exp2_results = await self._experiment_2_model_upgrade(sample, baseline_results)

        # Experiment 3: Temperature Tuning for Grounding
        print("\n" + "=" * 70)
        print("EXPERIMENT 3: Temperature Tuning (Improve Grounding)")
        print("=" * 70)
        exp3_results = await self._experiment_3_temperature_tuning(sample, baseline_results)

        # Summary and export
        self._export_results([baseline_results, exp1_results, exp2_results, exp3_results])

        return {
            'baseline': baseline_results,
            'experiment_1': exp1_results,
            'experiment_2': exp2_results,
            'experiment_3': exp3_results,
            'all_experiments': self.experiments
        }

    async def _run_baseline(self, products: List[Product]) -> Dict:
        """Baseline: 8B model with original prompt"""
        service = LLMService(model="meta-llama/Meta-Llama-3.1-8B-Instruct")
        results = []

        for i, product in enumerate(products, 1):
            desc, usage = await service.generate_description(
                system_prompt=PromptEngine.SYSTEM_PROMPT,
                user_prompt=PromptEngine.build_user_prompt(product),
                temperature=0.7,
                max_tokens=150
            )

            gen_result = GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=desc,
                latency_ms=usage['latency_ms'],
                input_tokens=usage['input_tokens'],
                output_tokens=usage['output_tokens'],
                cost_usd=self._calc_cost("meta-llama/Meta-Llama-3.1-8B-Instruct", usage)
            )

            eval_res = ManualEvaluator._score_description(gen_result)
            results.append({
                'product': product.product_name,
                'description': desc,
                'tokens_in': usage['input_tokens'],
                'tokens_out': usage['output_tokens'],
                'cost': gen_result.cost_usd,
                'ratings': eval_res['ratings'],
                'passes': eval_res['passes']
            })
            print(f"  ✓ {i}/{len(products)} - Pass: {eval_res['passes']}")

        pass_rate = (sum(1 for r in results if r['passes']) / len(results)) * 100
        total_cost = sum(r['cost'] for r in results)

        return {
            'name': 'BASELINE: 8B + Original Prompt',
            'model': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
            'temperature': 0.7,
            'prompt': 'Original system prompt',
            'description': 'Baseline generation with standard 8B model and original prompt',
            'rationale': 'Establishes baseline performance before improvements',
            'results': results,
            'pass_rate': pass_rate,
            'total_cost': total_cost,
            'avg_latency': sum(r['cost'] for r in results) / len(results) if results else 0
        }

    async def _experiment_1_prompt_engineering(self, products: List[Product], baseline: Dict) -> Dict:
        """Experiment 1: Enhanced prompt with stricter constraints"""
        service = LLMService(model="meta-llama/Meta-Llama-3.1-8B-Instruct")

        enhanced_prompt = """You are an expert e-commerce product description writer.

STRICT REQUIREMENTS:
1. LENGTH: Write exactly 50-90 words. Count every word. Show word count at end.
2. GROUNDING: Use ONLY attributes, material, warranty provided. Zero hallucinations.
3. GRAMMAR: Perfect spelling, punctuation, grammar. No errors allowed.
4. TONE: Professional and credible. Avoid hyperbole like "best" or "amazing."
5. STRUCTURE:
   - Sentence 1: What is the product and primary benefit?
   - Sentence 2-3: Key attributes from provided list
   - Sentence 4: Material quality and warranty
   - Sentence 5: Brief value statement

FORBIDDEN WORDS/PHRASES:
- "Best," "greatest," "amazing," "incredible," "revolutionary"
- Any claims not in the provided data
- Generic marketing clichés

Generate ONLY the description."""

        results = []
        for i, product in enumerate(products, 1):
            desc, usage = await service.generate_description(
                system_prompt=enhanced_prompt,
                user_prompt=PromptEngine.build_user_prompt(product),
                temperature=0.7,
                max_tokens=150
            )

            gen_result = GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=desc,
                latency_ms=usage['latency_ms'],
                input_tokens=usage['input_tokens'],
                output_tokens=usage['output_tokens'],
                cost_usd=self._calc_cost("meta-llama/Meta-Llama-3.1-8B-Instruct", usage)
            )

            eval_res = ManualEvaluator._score_description(gen_result)
            results.append({
                'product': product.product_name,
                'description': desc,
                'tokens_in': usage['input_tokens'],
                'tokens_out': usage['output_tokens'],
                'cost': gen_result.cost_usd,
                'ratings': eval_res['ratings'],
                'passes': eval_res['passes']
            })
            print(f"  ✓ {i}/{len(products)} - Pass: {eval_res['passes']}")

        pass_rate = (sum(1 for r in results if r['passes']) / len(results)) * 100
        improvement = pass_rate - baseline['pass_rate']
        total_cost = sum(r['cost'] for r in results)

        return {
            'name': 'EXP1: Enhanced Prompt Engineering',
            'model': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
            'temperature': 0.7,
            'prompt': 'Enhanced with stricter constraints',
            'description': 'Rewrote system prompt with explicit forbidding of superlatives and stricter length/grounding requirements',
            'rationale': 'Hypothesis: More explicit constraints force better grounding and reduce hallucinations',
            'what_changed': [
                'Added explicit word count requirement (50-90 words)',
                'Added forbidden words list (best, greatest, amazing, etc)',
                'Provided exact 5-sentence structure',
                'Emphasized "zero hallucinations" and grounding'
            ],
            'results': results,
            'pass_rate': pass_rate,
            'improvement': improvement,
            'total_cost': total_cost
        }

    async def _experiment_2_model_upgrade(self, products: List[Product], baseline: Dict) -> Dict:
        """Experiment 2: Upgrade to 70B model for better reasoning"""
        service = LLMService(model="meta-llama/Llama-3.3-70B-Instruct")

        results = []
        for i, product in enumerate(products, 1):
            desc, usage = await service.generate_description(
                system_prompt=PromptEngine.SYSTEM_PROMPT,
                user_prompt=PromptEngine.build_user_prompt(product),
                temperature=0.5,  # Lower temp for more factual output
                max_tokens=150
            )

            gen_result = GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=desc,
                latency_ms=usage['latency_ms'],
                input_tokens=usage['input_tokens'],
                output_tokens=usage['output_tokens'],
                cost_usd=self._calc_cost("meta-llama/Llama-3.3-70B-Instruct", usage)
            )

            eval_res = ManualEvaluator._score_description(gen_result)
            results.append({
                'product': product.product_name,
                'description': desc,
                'tokens_in': usage['input_tokens'],
                'tokens_out': usage['output_tokens'],
                'cost': gen_result.cost_usd,
                'ratings': eval_res['ratings'],
                'passes': eval_res['passes']
            })
            print(f"  ✓ {i}/{len(products)} - Pass: {eval_res['passes']}")

        pass_rate = (sum(1 for r in results if r['passes']) / len(results)) * 100
        improvement = pass_rate - baseline['pass_rate']
        total_cost = sum(r['cost'] for r in results)
        cost_increase = ((total_cost - baseline['total_cost']) / baseline['total_cost'] * 100) if baseline['total_cost'] > 0 else 0

        return {
            'name': 'EXP2: Model Upgrade to 70B',
            'model': 'meta-llama/Llama-3.3-70B-Instruct',
            'temperature': 0.5,
            'prompt': 'Original system prompt',
            'description': 'Switched from 8B to 70B model with better reasoning capabilities',
            'rationale': 'Hypothesis: Larger model has better reasoning for grounding and following complex instructions',
            'what_changed': [
                'Model: 8B → 70B-Instruct (8.75x more parameters)',
                'Temperature: 0.7 → 0.5 (more deterministic/factual)',
                'Same prompt, same task'
            ],
            'results': results,
            'pass_rate': pass_rate,
            'improvement': improvement,
            'total_cost': total_cost,
            'cost_increase_percent': cost_increase
        }

    async def _experiment_3_temperature_tuning(self, products: List[Product], baseline: Dict) -> Dict:
        """Experiment 3: Lower temperature for better grounding"""
        service = LLMService(model="meta-llama/Meta-Llama-3.1-8B-Instruct")

        # Test with temperature=0.3 (very factual, low creativity)
        results = []
        for i, product in enumerate(products, 1):
            desc, usage = await service.generate_description(
                system_prompt=PromptEngine.SYSTEM_PROMPT,
                user_prompt=PromptEngine.build_user_prompt(product),
                temperature=0.3,  # Lower temperature = more grounded
                max_tokens=150
            )

            gen_result = GenerationResult(
                product_name=product.product_name,
                product_attributes=product.attributes,
                material=product.material,
                warranty=product.warranty,
                generated_description=desc,
                latency_ms=usage['latency_ms'],
                input_tokens=usage['input_tokens'],
                output_tokens=usage['output_tokens'],
                cost_usd=self._calc_cost("meta-llama/Meta-Llama-3.1-8B-Instruct", usage)
            )

            eval_res = ManualEvaluator._score_description(gen_result)
            results.append({
                'product': product.product_name,
                'description': desc,
                'tokens_in': usage['input_tokens'],
                'tokens_out': usage['output_tokens'],
                'cost': gen_result.cost_usd,
                'ratings': eval_res['ratings'],
                'passes': eval_res['passes']
            })
            print(f"  ✓ {i}/{len(products)} - Pass: {eval_res['passes']}")

        pass_rate = (sum(1 for r in results if r['passes']) / len(results)) * 100
        improvement = pass_rate - baseline['pass_rate']
        total_cost = sum(r['cost'] for r in results)

        return {
            'name': 'EXP3: Temperature Tuning',
            'model': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
            'temperature': 0.3,
            'prompt': 'Original system prompt',
            'description': 'Reduced temperature from 0.7 to 0.3 for more factual, grounded outputs',
            'rationale': 'Hypothesis: Lower temperature reduces hallucinations and improves grounding accuracy',
            'what_changed': [
                'Temperature: 0.7 → 0.3 (deterministic rather than creative)',
                'Same model (8B), same prompt'
            ],
            'results': results,
            'pass_rate': pass_rate,
            'improvement': improvement,
            'total_cost': total_cost
        }

    def _calc_cost(self, model: str, usage: Dict) -> float:
        """Calculate cost from tokens"""
        model_cfg = self.config["models"].get(model, {})
        input_cost = (usage["input_tokens"] / 1_000_000) * model_cfg.get("input_cost_per_1m", 0)
        output_cost = (usage["output_tokens"] / 1_000_000) * model_cfg.get("output_cost_per_1m", 0)
        return input_cost + output_cost

    def _export_results(self, all_experiments: List[Dict]):
        """Export experiment results to CSV"""
        summary_data = []

        for exp in all_experiments:
            summary_data.append({
                'Experiment': exp['name'],
                'Model': exp['model'],
                'Temperature': exp['temperature'],
                'Pass Rate (%)': f"{exp['pass_rate']:.1f}%",
                'Improvement (%)': f"{exp.get('improvement', 0):+.1f}%",
                'Total Cost ($)': f"${exp['total_cost']:.4f}",
                'Description': exp['description']
            })

        df = pd.DataFrame(summary_data)
        df.to_csv('results/improvement_experiments.csv', index=False)
        print(f"\n✓ Experiment results saved to: results/improvement_experiments.csv")

        # Print summary table
        print("\n" + "=" * 120)
        print("IMPROVEMENT CYCLE SUMMARY")
        print("=" * 120)
        print(df.to_string(index=False))
        print("=" * 120)

        # Print detailed findings
        self._print_detailed_findings(all_experiments)

    def _print_detailed_findings(self, all_experiments: List[Dict]):
        """Print detailed findings for each experiment"""
        print("\nDETAILED FINDINGS:\n")

        for exp in all_experiments:
            print(f"\n{exp['name']}")
            print("-" * 80)
            print(f"What Changed: {', '.join(exp.get('what_changed', [exp['description']]))}")
            print(f"Why Expected to Help: {exp['rationale']}")
            print(f"Results:")
            print(f"  Pass Rate: {exp['pass_rate']:.1f}%")
            print(f"  Improvement: {exp.get('improvement', 0):+.1f}%")
            print(f"  Total Cost: ${exp['total_cost']:.4f}")

            if exp.get('cost_increase_percent'):
                print(f"  Cost Increase: {exp['cost_increase_percent']:+.1f}%")
