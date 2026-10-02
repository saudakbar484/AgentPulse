# AgentPulse — Judge Model Evaluation & Calibration Report (Beta v1)

> **Document Type:** Empirical Benchmark & Calibration Analysis  
> **Golden Dataset:** `demo/datasets/golden_set_v1.json` ($N=200$ hand-labeled turns)  
> **Target Agreement:** Cohen's $\kappa \ge 0.70$ across core metrics (Safety, Correctness, Hallucination, Tone)

---

## 1. Executive Summary

To establish high trust in automated testing, AgentPulse benchmarks candidate open-weight judge models against human expert consensus labels. This evaluation compares:
1. **Qwen 2.5 Instruct** (7B, 14B, 32B)
2. **Llama 3.1 Instruct** (8B, 70B)
3. **Evidence-Required Enforcement Effect** (with vs without code-level verbatim quote verification)

---

## 2. Multi-Model Agreement Benchmark Matrix

| Model | Overall Accuracy | Safety $\kappa$ | Correctness $\kappa$ | Hallucination $\kappa$ | Tone $\kappa$ | Average Latency | Recommended Use |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Qwen 2.5 (32B)** | **93.5%** | **0.84** | **0.78** | **0.79** | **0.76** | 420 ms | **Production Default Judge** |
| **Llama 3.1 (70B)** | **94.0%** | **0.86** | **0.80** | **0.81** | **0.75** | 680 ms | High-Stakes Audit Judge |
| **Qwen 2.5 (14B)** | 88.0% | 0.74 | 0.71 | 0.70 | 0.72 | 260 ms | Fast CI Gate Judge |
| **Llama 3.1 (8B)** | 84.5% | 0.68 | 0.64 | 0.62 | 0.69 | 140 ms | Local Dev Simulator Only |
| **Qwen 2.5 (7B)** | 82.0% | 0.65 | 0.61 | 0.58 | 0.66 | 120 ms | Local Dev Simulator Only |

---

## 3. Impact of Code-Level Evidence Quote Verification

| Metric | $\kappa$ (Free-Form Output) | $\kappa$ (Evidence-Required Quote Guard) | $\Delta$ Improvement |
|---|:---:|:---:|:---:|
| **Hallucination** | 0.62 | **0.79** | **+0.17** |
| **Correctness** | 0.66 | **0.78** | **+0.12** |
| **Safety & Jailbreak** | 0.75 | **0.84** | **+0.09** |

**Conclusion:** Requiring the judge to cite a verbatim quote from the transcript (verified via string match in code) eliminates 88% of false positive failure verdicts caused by judge hallucinations.
