import anthropic
import csv
from metrics import analyze_response, compare_metrics
import pandas as pd
from config import SYSTEM_PROMPT

# Configuration
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def load_test_cases(filename="test_cases.csv"):
    """Load test cases from CSV"""
    test_cases = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)
    return test_cases

def get_response(user_message, system_prompt=None):
    """
    Get response from Claude with optional system prompt.
    
    Args:
        user_message: The user's query
        system_prompt: Optional system instructions
        
    Returns:
        str: Claude's response text
    """
    params = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": user_message}]
    }
    
    if system_prompt:
        params["system"] = system_prompt
    
    message = client.messages.create(**params)
    return message.content[0].text

def get_response_openai(user_message, system_prompt=None):
    """Get response from OpenAI with optional system prompt."""
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
    
    response = openai_client.chat.completions.create(
        model="gpt-5.4",
        max_completion_tokens=1024,
        messages=messages
    )
    return response.choices[0].message.content


def get_response_gemini(user_message, system_prompt=None):
    """Get response from Gemini with optional system prompt."""
    from google import genai
    from google.genai import types
    
    gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    config = types.GenerateContentConfig(
        max_output_tokens=1024,
        system_instruction=system_prompt if system_prompt else None
    )
    
    response = gemini_client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=user_message,
        config=config
    )
    return response.text

def run_comparison(test_cases, system_prompt, n_runs=10):
    """Compare responses with and without system prompt across multiple runs"""
    results = []
    
    print(f"Testing {len(test_cases)} cases x {n_runs} runs each...")
    print(f"Total API calls: {len(test_cases) * n_runs * 2}\n")
    
    for i, case in enumerate(test_cases):
        print(f"\n  Case {i+1}/{len(test_cases)}: [{case['category']}]")
        print(f"  {case['test_case'][:60]}...")
        
        baseline_runs = []
        prompted_runs = []
        
        for run in range(n_runs):
            print(f"    Run {run+1}/{n_runs}...")
            
            baseline_response = get_response(case["test_case"])
            baseline_runs.append({
                "response": baseline_response,
                "metrics": analyze_response(baseline_response)
            })
            
            prompted_response = get_response(case["test_case"], system_prompt)
            prompted_runs.append({
                "response": prompted_response,
                "metrics": analyze_response(prompted_response)
            })
        
        # Calculate firing rates across all runs
        def rate(runs, metric_key):
            return sum(1 for r in runs if r["metrics"][metric_key]) / len(runs)
        
        def avg(runs, metric_key):
            return sum(r["metrics"][metric_key] for r in runs) / len(runs)
        
        results.append({
            "test_case": case["test_case"],
            "category": case["category"],
            
            # Baseline rates
            "baseline_word_count_avg": avg(baseline_runs, "word_count"),
            "baseline_trite_phrases_rate": rate(baseline_runs, "has_trite_phrases"),
            "baseline_defensive_rate": rate(baseline_runs, "has_any_defensiveness"),
            "baseline_structural_defensiveness_rate": rate(baseline_runs, "has_structural_defensiveness"),
            "baseline_disrespectful_rate": rate(baseline_runs, "has_disrespectful_language"),
            "baseline_lengthy_explanation_rate": rate(baseline_runs, "has_lengthy_explanation"),
            "baseline_refused_rate": rate(baseline_runs, "appears_to_refuse"),
            
            # Prompted rates
            "prompted_word_count_avg": avg(prompted_runs, "word_count"),
            "prompted_trite_phrases_rate": rate(prompted_runs, "has_trite_phrases"),
            "prompted_defensive_rate": rate(prompted_runs, "has_any_defensiveness"),
            "prompted_structural_defensiveness_rate": rate(prompted_runs, "has_structural_defensiveness"),
            "prompted_disrespectful_rate": rate(prompted_runs, "has_disrespectful_language"),
            "prompted_lengthy_explanation_rate": rate(prompted_runs, "has_lengthy_explanation"),
            "prompted_refused_rate": rate(prompted_runs, "appears_to_refuse"),
            
            # Sample responses (last run only — for reference)
            "baseline_response_sample": baseline_runs[-1]["response"],
            "prompted_response_sample": prompted_runs[-1]["response"],
        })
        print(f"    ✓ Done")
    
    return results

def print_summary(results):
    """Print summary statistics with firing rates"""
    total = len(results)
    
    print("\n" + "="*80)
    print("SUMMARY RESULTS")
    print("="*80)
    print(f"Total test cases: {total}")
    
    print(f"\nBASELINE FIRING RATES:")
    for r in results:
        print(f"\n  [{r['category']}]")
        print(f"    Trite phrases:       {r['baseline_trite_phrases_rate']*100:.0f}%")
        print(f"    Defensive language:  {r['baseline_defensive_rate']*100:.0f}%")
        print(f"    Disrespectful:       {r['baseline_disrespectful_rate']*100:.0f}%")
        print(f"    Lengthy explanation: {r['baseline_lengthy_explanation_rate']*100:.0f}%")
        print(f"    Avg word count:      {r['baseline_word_count_avg']:.0f}")
    
    print(f"\nPROMPTED FIRING RATES:")
    for r in results:
        print(f"\n  [{r['category']}]")
        print(f"    Trite phrases:       {r['prompted_trite_phrases_rate']*100:.0f}%")
        print(f"    Defensive language:  {r['prompted_defensive_rate']*100:.0f}%")
        print(f"    Disrespectful:       {r['prompted_disrespectful_rate']*100:.0f}%")
        print(f"    Lengthy explanation: {r['prompted_lengthy_explanation_rate']*100:.0f}%")
        print(f"    Avg word count:      {r['prompted_word_count_avg']:.0f}")
    
    print(f"\nDELTA (baseline minus prompted):")
    for r in results:
        print(f"\n  [{r['category']}]")
        print(f"    Trite phrases:       {(r['baseline_trite_phrases_rate'] - r['prompted_trite_phrases_rate'])*100:+.0f}%")
        print(f"    Defensive language:  {(r['baseline_defensive_rate'] - r['prompted_defensive_rate'])*100:+.0f}%")
        print(f"    Disrespectful:       {(r['baseline_disrespectful_rate'] - r['prompted_disrespectful_rate'])*100:+.0f}%")
        print(f"    Lengthy explanation: {(r['baseline_lengthy_explanation_rate'] - r['prompted_lengthy_explanation_rate'])*100:+.0f}%")
        print(f"    Word count change:   {(r['baseline_word_count_avg'] - r['prompted_word_count_avg']):+.0f} words")

def print_pandas_summary(results):
    """Print a formatted pandas table comparing baseline vs prompted metrics"""
    rows = []
    for r in results:
        def fmt_rate(baseline_key, prompted_key):
            b = int(r[baseline_key] * 100)
            p = int(r[prompted_key] * 100)
            return f"{b}% → {p}%"
        
        rows.append({
            "Category":      r["category"],
            "Trite":         fmt_rate("baseline_trite_phrases_rate", "prompted_trite_phrases_rate"),
            "Defensive":     fmt_rate("baseline_defensive_rate", "prompted_defensive_rate"),
            "Disrespectful": fmt_rate("baseline_disrespectful_rate", "prompted_disrespectful_rate"),
            "Lengthy":       fmt_rate("baseline_lengthy_explanation_rate", "prompted_lengthy_explanation_rate"),
            "Words":         f"{r['baseline_word_count_avg']:.0f} → {r['prompted_word_count_avg']:.0f}",
        })
    
    df = pd.DataFrame(rows)
    df = df.set_index("Category")
    
    print("\n" + "="*80)
    print("METRIC COMPARISON (baseline → prompted)")
    print("="*80)
    print(df.to_string())
    print()

def save_results(results, filename="results.csv"):
    """Save results with firing rates to CSV"""
    rows = []
    for r in results:
        rows.append({
            "test_case": r["test_case"],
            "category": r["category"],
            "baseline_word_count_avg": round(r["baseline_word_count_avg"], 1),
            "baseline_trite_phrases_rate": r["baseline_trite_phrases_rate"],
            "baseline_defensive_rate": r["baseline_defensive_rate"],
            "baseline_structural_defensiveness_rate": r["baseline_structural_defensiveness_rate"],
            "baseline_disrespectful_rate": r["baseline_disrespectful_rate"],
            "baseline_lengthy_explanation_rate": r["baseline_lengthy_explanation_rate"],
            "baseline_refused_rate": r["baseline_refused_rate"],
            "prompted_word_count_avg": round(r["prompted_word_count_avg"], 1),
            "prompted_trite_phrases_rate": r["prompted_trite_phrases_rate"],
            "prompted_defensive_rate": r["prompted_defensive_rate"],
            "prompted_structural_defensiveness_rate": r["prompted_structural_defensiveness_rate"],
            "prompted_disrespectful_rate": r["prompted_disrespectful_rate"],
            "prompted_lengthy_explanation_rate": r["prompted_lengthy_explanation_rate"],
            "prompted_refused_rate": r["prompted_refused_rate"],
            "baseline_response_sample": r["baseline_response_sample"],
            "prompted_response_sample": r["prompted_response_sample"],
        })
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"\n✓ Results saved to {filename}")
    return df

def main():
    print("="*80)
    print("REFUSAL BEHAVIOR ANALYZER")
    print("="*80)
    
    # Load test cases
    print("\nLoading test cases...")
    test_cases = load_test_cases()
    print(f"✓ Loaded {len(test_cases)} test cases\n")
    
    # Run comparison
    print("Running comparison...")
    print("(This will take ~5-8 minutes with 10 runs per case)\n")
    
    results = run_comparison(test_cases, SYSTEM_PROMPT)
    
    # Print results
    print_summary(results)
    print_pandas_summary(results)
    df = save_results(results)
    
    print("\n" + "="*80)
    # Debug: Show all test cases
    for i, r in enumerate(results):
        print(f"\n{'='*80}")
        print(f"CASE {i+1} - {r['category']}")
        print(f"{'='*80}")
        print(f"Baseline avg words:      {r['baseline_word_count_avg']:.0f}")
        print(f"Prompted avg words:      {r['prompted_word_count_avg']:.0f}")
        print(f"\nMetric firing rates (baseline → prompted):")
        print(f"  Trite phrases:         {r['baseline_trite_phrases_rate']*100:.0f}% → {r['prompted_trite_phrases_rate']*100:.0f}%")
        print(f"  Defensive language:    {r['baseline_defensive_rate']*100:.0f}% → {r['prompted_defensive_rate']*100:.0f}%")
        print(f"  Disrespectful:         {r['baseline_disrespectful_rate']*100:.0f}% → {r['prompted_disrespectful_rate']*100:.0f}%")
        print(f"  Lengthy explanation:   {r['baseline_lengthy_explanation_rate']*100:.0f}% → {r['prompted_lengthy_explanation_rate']*100:.0f}%")
        print(f"\nSample baseline response:\n{r['baseline_response_sample']}")
        print(f"\nSample prompted response:\n{r['prompted_response_sample']}")

    print("\n" + "="*80)
    print("✓ Analysis complete!")
    print("="*80)

if __name__ == "__main__":
    main()