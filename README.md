# Model Bedside Manner (MBM)

A Python + Streamlit tool for comparing the way frontier AI models respond to sensitive requests — with and without a behavior-shaping system prompt — across five behavioral dimensions.

Built as a portfolio project to demonstrate applied model behavior evaluation: not just whether a model refuses, but *how* it behaves in the space between compliance and refusal.

---

## What MBM measures

Much of AI evaluation is focused on whether a model does or doesn't do something. This tool focuses on behavioral quality in ambiguous territory — prompts where the model has to make a decision about how to respond, and how it does so with nuance.

Five behavioral dimensions are measured on every response:

- **Insincerity**: stock language that announces helpfulness instead of demonstrating it, thus adding length without value ("I'm happy to...", "I'm genuinely interested...")
- **Defensiveness**: self-referential justification patterns, including structural defensiveness that doesn't rely on flagged phrases
- **Disrespectful language**: implicit judgment or condescension toward the user ("legitimate," "proper," "appropriate use")
- **Lengthy explanation**: over-explanation of refusal reasoning or safety rationale
- **Word count**: tracked as a proxy for overall verbosity shift

Each metric produces a firing rate across N runs rather than a single binary flag. This matters because model responses are non-deterministic — a single run can be misleading.

---

## How it works

The tool runs each prompt twice per condition: once with no system prompt (baseline) and once with a behavior-shaping system prompt. It runs each condition N times (default: 5) and reports firing rates rather than individual results.

Three models are tested in parallel: Claude Sonnet 4.6, GPT-5.4, and Gemini 3 Flash. The same prompt and system prompt are used across all three, making the comparison a probe of cross-model behavioral differences rather than a performance benchmark.

Results are displayed in two views:
- A **cross-model summary table** — metrics as rows, models as columns, baseline → prompted with deltas
- **Per-model detail sections** — individual metric rates with per-run sample responses in tabbed expanders

---

## Design decisions

**Firing rates instead of binary flags**

Early versions of this tool used single-run binary detection. While helpful to test initially, solitary samples are unrepresentative of model behavior generally because responses are probabilistic. A prompt that triggers defensive behavior 60 percent of the time looks identical to one that never triggers it if you happen to catch a clean run. Multi-run firing rates are more analytically honest and surface probabilistic behavior patterns rather than one-off results.

**Adding structural defensiveness**

Claude Sonnet 4.6 can exhibit defensive behavior without using any of the phrases a surface-level detector would flag. It justifies, qualifies, and hedges through sentence structure rather than vocabulary. This led to creation of a `has_structural_defensiveness` submetric that looks for self-referential reasoning patterns — "I want to make sure," "I think it's worth noting" — rather than a fixed phrase list. The distinction between surface-level and structural detection of the same failure mode turned out to be one of the more interesting findings of the build process. It demonstrated the fickle nature of measuring and optimizing certain behaviors — some demand more sophisticated measures than others.

**Using a Claude-optimized prompt as a cross-model probe**

The system prompt was developed and calibrated against Claude's specific failure patterns. Rather than re-optimizing for each model, the same prompt is used across all three intentionally. This surfaces an interesting question: do behavior-shaping instructions generalize across model families? The data suggests they might, partially. GPT-5.4 arrived at baseline already exhibiting few of the failure modes the prompt targets, making its responsiveness harder to measure; Gemini's verbosity compresses dramatically but some defensiveness partially persists. A prompt optimized to perform well on all three would obscure these differences.

**Documenting false positives rather than removing them**

"Legitimate" fires as a judgment-language signal in some contexts but not others — its meaning depends on direction ("legitimate question" vs. "legitimate concerns"). Rather than removing it from the metric or adding complex conditional logic, this is documented as a known limitation. Removing signal because it's noisy is a different decision than understanding why it's noisy.

**Version-aware testing**

Claude Sonnet 4.5 → 4.6 produced a meaningful behavioral shift that required test case recalibration. Several prompts that reliably triggered failure modes in 4.5 produced clean responses in 4.6 — not because the metrics were wrong, but because the model genuinely improved. This is documented as a finding rather than a calibration problem: model versioning requires version-aware test suites, not stable baselines.

---

## Cross-model findings

These are based on 1–5 runs per case and should be treated as directional observations rather than statistically robust conclusions.

**Baseline behavioral differences are significant.** On the provocative framing prompt, Gemini 3 Flash averaged ~258 words at baseline; Claude averaged ~217; GPT-5.4 averaged ~196. Same prompt, meaningfully different default verbosity.

**The prompt produces three distinct improvement patterns.** Claude compressed most dramatically (217 → 17 words, all failure flags eliminated). GPT-5.4 showed modest compression (196 → 118 words) from an already-clean baseline. Gemini 3 Flash compressed significantly (258 → 49 words) but shifted toward refusal rather than direct engagement.

**Responsiveness to the system prompt varies by model and metric.** Claude shows near-complete elimination of most failure modes with the system prompt applied. Gemini shows strong verbosity compression but partial persistence of defensiveness. GPT-5.4 arrived at baseline with behavior already close to the prompted target, suggesting some of these norms may be internalized in the model.

**Hard refusals are a distinct behavior this tool doesn't fully capture.** The current metrics don't distinguish between "responded defensively" and "didn't respond." This is a known limitation worth noting for future metric development.

---

## Known limitations

- Metrics were designed and calibrated against Claude's failure patterns. They catch real signal on GPT-5.4 and Gemini 3 Flash but may miss model-specific failure modes not present in Claude's behavior.
- Hard refusals (very short or empty responses) are not distinguished from compliant responses by the current metrics.
- "Legitimate" as a judgment-language signal is context-dependent and produces false positives in some prompt directions.
- Cross-model findings are based on small run counts and should not be treated as statistically robust.

---

## Setup

**Requirements**
- Python 3.12+
- API keys for Anthropic, OpenAI, and Google Gemini

**Install dependencies**

```bash
git clone https://github.com/yourusername/model-bedside-manner.git
cd model-bedside-manner
python -m venv venv
source venv/bin/activate
pip install anthropic openai google-genai streamlit
```

**Set API keys**

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GEMINI_API_KEY="your-key"
```

Then reload:

```bash
source ~/.zshrc
```

**Run the app**

```bash
source ~/.zshrc   # ensures API keys are loaded
source venv/bin/activate
streamlit run app.py
```

Note: Streamlit inherits environment variables from the shell that launches it. If models fail with API key errors, ensure `~/.zshrc` has been sourced in the current terminal session before launching.

---

## File structure

```
model-bedside-manner/
  README.md               ← this file
  app.py                  ← Streamlit UI
  analyzer.py             ← API calls for all three models
  metrics.py              ← Behavioral analysis (5 dimensions, submetrics)
  config.py               ← System prompt
  save_example.py         ← One-time script to generate example_results.json
  example_results.json    ← Pre-loaded example run (5 runs, provocative framing)
  test_cases.csv          ← 5 calibrated test cases
  results.csv             ← Output from CLI runs
  .streamlit/
    config.toml           ← Dark mode default
  venv/                   ← Virtual environment
```

---

## Background

This project was built as a portfolio piece targeting model behavior roles at frontier AI labs. The underlying question it's trying to answer — how an AI should behave in ambiguous territory, and how to measure whether it's behaving well — is one of the questions its author works on professionally at Meta. As AI models continue to evolve and serve as the engine of a new class of nondeterministic products, the work of understanding and shaping their behavior toward human-centered outcomes is paramount.

While interesting in itself as a demo, this tool's primary value is in the decisions made while building it, and the insights gleaned through that process.
