# Model Bedside Manner (MBM)

A Python + Streamlit tool for comparing the way frontier AI models respond to sensitive prompts — with and without a behavior-shaping system prompt — across five behavioral dimensions.

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

Three models are tested in parallel: Claude Sonnet 5, GPT-5.5, and Gemini 3.5 Flash. These are the default recommended model at each lab for everyday use, not necessarily each provider's most expensive or most recently released option. The same prompt and system prompt are used across all three, making the comparison a probe of cross-model behavioral differences rather than a performance benchmark.

Results are displayed in two views:
- A **cross-model summary table** — metrics as rows, models as columns, baseline → prompted with deltas
- **Per-model detail sections** — individual metric rates with per-run sample responses in tabbed expanders

---

## Design decisions

**Firing rates instead of binary flags**

Early versions of this tool used single-run binary detection. While helpful to test initially, solitary samples are unrepresentative of model behavior generally because responses are probabilistic. A prompt that triggers defensive behavior 60 percent of the time looks identical to one that never triggers it if you happen to catch a clean run. Multi-run firing rates are more analytically honest and surface probabilistic behavior patterns rather than one-off results.

**Adding structural defensiveness**

Claude models can exhibit defensive behavior without using any of the phrases a surface-level detector would flag. They justify, qualify, and hedge through sentence structure rather than vocabulary. This led to creation of a `has_structural_defensiveness` submetric that looks for self-referential reasoning patterns — "I want to make sure," "I think it's worth noting" — rather than a fixed phrase list. The distinction between surface-level and structural detection of the same failure mode turned out to be one of the more interesting findings of the build process. It demonstrated the fickle nature of measuring and optimizing certain behaviors — some demand more sophisticated measures than others.

**Using a Claude-optimized prompt as a cross-model probe**

The system prompt was developed and calibrated against Claude's specific failure patterns. Rather than re-optimizing for each model, the same prompt is used across all three intentionally. This surfaces an interesting question: do behavior-shaping instructions generalize across model families? See Cross-model findings below for what the data shows.

**Documenting false positives rather than removing them**

"Legitimate" fires as a judgment-language signal in some contexts but not others — its meaning depends on direction ("legitimate question" vs. "legitimate concerns"). Rather than removing it from the metric or adding complex conditional logic, this is documented as a known limitation. Removing signal because it's noisy is a different decision than understanding why it's noisy.

**Evolving the lengthy explanation metric as models evolve**

The original verbose_non_refusal submetric required both high word count and a stock insincerity phrase to fire, which worked well against 4.6-era responses. After migrating to Sonnet 5, several long, substantive redirects (asking clarifying questions, offering alternatives) evaded detection altogether because they didn't use stock phrases, despite being functionally similar to the responses the metric was designed to catch. Instead of marking this aspect for test cases "resolved," the metric was updated: a new substantial_redirect submetric fires on word count and non-refusal status alone, independent of phrase matching. This preserves the original threshold while removing an accidental dependency on a specific rhetorical style. It follows the same principle behind "legitimate" false positives: when a model changes, what matters isn't just whether the test cases still work, but if the metrics still measure what they're supposed to.

**Version-aware testing**

Claude Sonnet 4.5 → 4.6 produced a meaningful behavioral shift that called for test case recalibration. The same thing happened again when migrating to Sonnet 5: the creative wrapper test case stopped triggering any failure modes at baseline, having apparently been resolved by the model's improvements. It was replaced with a new case — a forced-choice prompt that surfaces structural defensiveness in a different context (a direct opinion request rather than a sensitive-content request). This is documented as a finding rather than a calibration problem in that model versioning requires version-aware test suites, not stable baselines, and sometimes requires new test cases entirely, not just re-running the old ones.

---

## Cross-model findings

These are based on 10 runs per case (100 total API calls: 5 test cases × 2 conditions × 10 runs) and represent a more statistically stable sample than the original 1–5 run findings.

**The system prompt remains very effective on Claude.** Provocative framing shows defensiveness dropping from 20%→0%, disrespectful language 10%→0%, lengthy explanation 70%→0%, and word count compressing from 172→11. Forced choice (the new test case) shows lengthy explanation eliminated entirely, 100%→0%, alongside a clean removal of the structural defensiveness pattern ("here's my actual reasoning, not a hedge") observed in manual testing.

**Ambiguous intent still demonstrates the "legitimate" false positive.** The word fires as a disrespectful-language signal at 100% baseline and persists at 70% even after prompting — consistent with the original finding that this is a context-dependent false positive rather than a bug to fix.

**Gray area is the one case where the system prompt doesn't improve on lengthy explanation** — 100% baseline, 100% prompted. Reading the actual responses shows why: the prompted version doesn't hedge or moralize, it asks specific, reasonable clarifying questions before drafting emotionally weighted content. The substantial_redirect submetric can't distinguish a defensive redirect from a genuinely appropriate one — length and non-refusal are reasonable proxies for defensiveness on most prompts, but they break down when the right response to a request is to ask more before acting. This is documented as a known limitation rather than patched further.

**Emotional leverage shows a distinct improvement pattern from insincerity.** Trite phrase detection stays flat (10%→10%) since Sonnet 5's redirects on this prompt rarely use the specific stock phrases the metric tracks — but lengthy explanation still drops meaningfully (100%→0%), showing the system prompt's effect on redirect length even where phrase-based insincerity detection stays noisy.

**GPT-5.5 and Gemini 3.5 Flash show different baselines than their predecessors.** GPT-5.5 arrives at baseline already close to clean across most metrics — consistent with the pattern observed in the original GPT-5.4 comparison, suggesting some of these behavioral norms may be increasingly internalized in OpenAI's models rather than requiring prompting. Gemini 3.5 Flash shows the most baseline verbosity (overly_verbose_refusal firing on most runs) with strong compression after prompting, similar to the compression pattern seen in the original Gemini 3 Flash data.

---

## Known limitations

- Metrics were designed and calibrated against Claude's failure patterns. They catch real signal on GPT-5.5 and Gemini 3.5 Flash but may miss model-specific failure modes not present in Claude's behavior.
- Hard refusals (very short or empty responses) are not distinguished from compliant responses by the current metrics.
- "Legitimate" as a judgment-language signal is context-dependent and produces false positives in some prompt directions.
- substantial_redirect (part of the lengthy explanation metric) doesn't distinguish a defensive redirect from a genuinely helpful one — a long response that asks clarifying questions before proceeding will fire the same as a long response that hedges and moralizes. This surfaced clearly in the gray area test case after the Sonnet 5 migration.
- Cross-model findings are based on 10 runs per case per condition and should be treated as directional, not as statistically definitive.
- Test cases require periodic recalibration as models evolve. One of the original five (creative wrapper) stopped triggering meaningful signal after the Sonnet 5 migration and was replaced with a forced-choice prompt targeting structural defensiveness instead.

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

**A note on Gemini's thinking tokens**
Gemini 3 and 3.5 models have thinking enabled by default, and max_output_tokens acts as a combined budget for both thinking and visible output — not just output alone. Without capping thinking, responses can be truncated mid-sentence. analyzer.py sets thinking_level="low" and a higher max_output_tokens ceiling (2048) to leave enough room for complete responses given this tool's conversational, non-reasoning-heavy prompts.

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
