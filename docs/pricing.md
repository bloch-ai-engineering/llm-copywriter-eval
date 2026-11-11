# Nebius Token Factory - Pricing & Model Reference

## 💰 Pricing Summary

All prices from Nebius Token Factory (USD per 1M tokens)

| Model | Input | Output | Use Case | Throughput |
|-------|-------|--------|----------|-----------|
| **Meta-Llama-3.1-8B** | $0.02 | $0.06 | Fast, cost-effective | 30 Tok/s |
| **Meta-Llama-3.3-70B** | $0.13 | $0.40 | Best quality, reasoning | 25 Tok/s |
| **Gemma-2-9b** | $0.03 | $0.09 | Balanced quality/cost | 90 Tok/s |

## 📊 Cost Examples

### 100 products, 50-90 word descriptions

**8B Model (Fast, Budget)**
- Avg input tokens: 250 (prompt + product data)
- Avg output tokens: 100 (description)
- Per request: (250/1M × $0.02) + (100/1M × $0.06) = **$0.000013**
- For 100 products: **~$0.0013** (negligible)
- Best for: Task 2 baseline generation

**70B Model (Best Quality - RECOMMENDED)**
- Avg input tokens: 250
- Avg output tokens: 100
- Per request: (250/1M × $0.13) + (100/1M × $0.40) = **$0.0000685**
- For 100 products: **~$0.007** (5x cheaper than before!)
- Best for: Task 4 improvements, production quality
- ✨ **New lower pricing makes this the sweet spot!**

**Gemma-2-9b (Balanced)**
- Avg input tokens: 250
- Avg output tokens: 100
- Per request: (250/1M × $0.03) + (100/1M × $0.09) = **$0.000018**
- For 100 products: **~$0.002**

## 🎯 Model Selection Guide

### Choose 8B Model When:
- ✓ Budget is tight
- ✓ Speed is critical
- ✓ Simple descriptions needed
- ✓ Testing/development
- Suitable for Task 2 baseline

### Choose 70B Model When:
- ✓ Quality is paramount
- ✓ Complex reasoning needed
- ✓ Production deployment
- ✓ High pass rates required
- Suitable for Task 4 improvements

### Choose Gemma When:
- ✓ Need balanced performance
- ✓ Prefer faster inference
- ✓ Limited context needed (8K)
- ✓ Alternative to Llama

## 📋 Model Specifications

### Meta-Llama-3.1-8B-Instruct
```
Architecture: 8 Billion Parameters
Context: 128K tokens
Quantization: fp8
Throughput: 30 tokens/second
License: Llama 3.1 License
Reasoning: General purpose
Tool Calling: Available
```

### Meta-Llama-3.3-70B-Instruct
```
Architecture: 70 Billion Parameters
Context: 128K tokens
Quantization: fp8
Throughput: 25 tokens/second
License: Llama 3.3 License
Reasoning: Excellent
Tool Calling: Available
Best for: Reasoning-heavy tasks
Pricing: $0.13 (in) / $0.40 (out) per 1M tokens
```

### Gemma-2-9b-it
```
Architecture: 9 Billion Parameters
Context: 8K tokens
Quantization: fp8
Throughput: 90 tokens/second
License: Gemma License
Reasoning: Good
Tool Calling: N/A
Best for: Chat and coding
```

## 💡 Cost Optimization Tips

1. **Batch requests**: Process multiple descriptions per API call
2. **Start with 8B**: Prove concept before upgrading to 70B
3. **Monitor tokens**: Track actual usage vs estimates
4. **Set max_tokens**: Limit output to necessary length
5. **Cache prompts**: Reuse system prompts efficiently

## 🔄 Token Counting

**Approximate**:
- 1 token ≈ 4 characters
- Average English word ≈ 1.3 tokens
- Product description (60 words) ≈ 80 tokens

**Actual**:
- Use API response `usage` field for exact counts
- Our code captures real counts in `input_tokens` and `output_tokens`

## 📈 Pricing Tiers

For large-scale deployments, contact Nebius for volume discounts:
- 1K-10K requests/month
- 10K-100K requests/month
- 100K+ requests/month

## 🌍 Regions

All models available in:
- **eu-north1** (Stockholm)
- Other regions available upon request

---

**Last updated**: 2024
**Source**: Nebius Token Factory API
**Task**: Assignment - LLM Product Descriptions Evaluation
