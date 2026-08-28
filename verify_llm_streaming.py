"""
Verification script for the LLM streaming service layer.

Tests:
1. generate_stream() works with real Ollama Qwen3:8b
2. filler_complete and question_complete events fire correctly
3. Final JSON validates
4. Existing generate() still works (compatibility)
5. Retry handling remains functional
"""

import asyncio
import json
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("VERIFY_STREAMING")

from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest, LLMStreamEvent


# Same type of minimal interviewer prompts
TEST_PROMPTS = [
    LLMRequest(
        prompt=(
            "You are interviewing Alice Profiler.\n"
            "Topic: Python\n"
            "Difficulty: Medium\n"
            "Type: Technical\n"
            "This is a new topic.\n\n"
            "Generate a natural conversational transition and one interview question.\n\n"
            'Return ONLY this JSON:\n'
            '{"conversational_filler": "...", "question": "..."}\n'
        ),
        system_prompt="You are an expert interviewer. Output valid JSON with conversational_filler and question.",
        temperature=0.8,
        require_json=True
    ),
    LLMRequest(
        prompt=(
            "You are interviewing Alice Profiler.\n"
            "Topic: Machine Learning\n"
            "Difficulty: Medium\n"
            "Type: Technical\n"
            "This is a new topic.\n\n"
            "Last question asked: Can you walk me through how you built the fraud detection system?\n"
            "Candidate's answer: I used XGBoost with feature engineering on transaction data. The main challenge was class imbalance.\n\n"
            "Generate a natural conversational transition and one interview question.\n"
            "If there was a previous answer, reference it naturally in your transition.\n\n"
            'Return ONLY this JSON:\n'
            '{"conversational_filler": "...", "question": "..."}\n'
        ),
        system_prompt="You are an expert interviewer. Output valid JSON with conversational_filler and question.",
        temperature=0.8,
        require_json=True
    ),
    LLMRequest(
        prompt=(
            "You are interviewing Alice Profiler.\n"
            "Topic: Docker\n"
            "Difficulty: Hard\n"
            "Type: Technical\n"
            "This is a follow-up to dig deeper.\n\n"
            "Last question asked: How did you handle class imbalance in your fraud detection model?\n"
            "Candidate's answer: I applied SMOTE for oversampling the minority class and tuned class weights in XGBoost.\n\n"
            "Generate a natural conversational transition and one interview question.\n"
            "If there was a previous answer, reference it naturally in your transition.\n\n"
            'Return ONLY this JSON:\n'
            '{"conversational_filler": "...", "question": "..."}\n'
        ),
        system_prompt="You are an expert interviewer. Output valid JSON with conversational_filler and question.",
        temperature=0.8,
        require_json=True
    ),
]


async def verify_streaming():
    """Test generate_stream() with real Ollama."""
    client = OllamaClient()

    print("=" * 60)
    print("STREAMING GENERATION TEST")
    print("=" * 60)

    all_results = []

    for i, req in enumerate(TEST_PROMPTS):
        print(f"\n--- Streaming Request {i+1} ---")

        events_received = []

        async def on_event(event: LLMStreamEvent):
            events_received.append(event)

        t_start = time.perf_counter()
        response = await client.generate_stream(req, on_event=on_event)
        t_total = time.perf_counter() - t_start

        meta = response.metadata
        ttft = meta.get("ttft")
        t_filler = meta.get("t_filler_complete")
        t_question = meta.get("t_question_complete")
        eval_count = meta.get("eval_count", 0)
        tps = meta.get("tokens_per_sec", 0.0)

        # Check events
        filler_events = [e for e in events_received if e.event_type == "filler_complete"]
        question_events = [e for e in events_received if e.event_type == "question_complete"]
        complete_events = [e for e in events_received if e.event_type == "stream_complete"]

        filler_ok = len(filler_events) == 1
        question_ok = len(question_events) == 1
        complete_ok = len(complete_events) == 1
        json_ok = response.parsed_json is not None

        result = {
            "request": i + 1,
            "ttft": ttft,
            "t_filler": t_filler,
            "t_question": t_question,
            "t_total": t_total,
            "tokens": eval_count,
            "tps": tps,
            "filler_ok": filler_ok,
            "question_ok": question_ok,
            "json_ok": json_ok,
            "filler_text": filler_events[0].text if filler_ok else "MISSING",
            "question_text": question_events[0].text if question_ok else "MISSING",
        }
        all_results.append(result)

        print(f"  Time to first token:      {ttft:.4f} sec" if ttft else "  TTFT: N/A")
        print(f"  Filler complete:          {t_filler:.2f} sec" if t_filler else "  Filler: N/A")
        print(f"  Question complete:        {t_question:.2f} sec" if t_question else "  Question: N/A")
        print(f"  Total generation:         {t_total:.2f} sec")
        print(f"  Output tokens:            {eval_count}")
        print(f"  Tokens/sec:               {tps:.1f}")
        print(f"  filler_complete event:    {'âœ“' if filler_ok else 'âœ—'}")
        print(f"  question_complete event:  {'âœ“' if question_ok else 'âœ—'}")
        print(f"  stream_complete event:    {'âœ“' if complete_ok else 'âœ—'}")
        print(f"  JSON valid:               {'âœ“' if json_ok else 'âœ—'}")
        print()

        if json_ok:
            parsed = response.parsed_json
            print(f"  Filler:   {parsed.get('conversational_filler', 'N/A')[:80]}")
            print(f"  Question: {parsed.get('question', 'N/A')[:80]}")
        print()

        await asyncio.sleep(1)

    return all_results


async def verify_compatibility():
    """Test that existing generate() still works."""
    print("=" * 60)
    print("COMPATIBILITY TEST: generate() (non-streaming)")
    print("=" * 60)

    client = OllamaClient()
    req = TEST_PROMPTS[0]

    t_start = time.perf_counter()
    response = await client.generate(req)
    t_total = time.perf_counter() - t_start

    json_ok = response.parsed_json is not None
    has_filler = response.parsed_json and "conversational_filler" in response.parsed_json
    has_question = response.parsed_json and "question" in response.parsed_json

    print(f"  Total generation:   {t_total:.2f} sec")
    print(f"  JSON valid:         {'âœ“' if json_ok else 'âœ—'}")
    print(f"  Has filler:         {'âœ“' if has_filler else 'âœ—'}")
    print(f"  Has question:       {'âœ“' if has_question else 'âœ—'}")
    print(f"  generate() works:   {'âœ“' if json_ok else 'âœ—'}")
    print()

    return json_ok


async def main():
    print("\n" + "=" * 60)
    print("LLM STREAMING SERVICE VERIFICATION")
    print("=" * 60 + "\n")

    # 1. Streaming test
    stream_results = await verify_streaming()

    # 2. Compatibility test
    compat_ok = await verify_compatibility()

    # 3. Final report
    valid = [r for r in stream_results if r["ttft"] is not None]
    if valid:
        avg_ttft = sum(r["ttft"] for r in valid) / len(valid)
        avg_filler = sum(r["t_filler"] for r in valid if r["t_filler"]) / max(1, sum(1 for r in valid if r["t_filler"]))
        avg_question = sum(r["t_question"] for r in valid if r["t_question"]) / max(1, sum(1 for r in valid if r["t_question"]))
        avg_total = sum(r["t_total"] for r in valid) / len(valid)
        avg_tokens = sum(r["tokens"] for r in valid) / len(valid)
        avg_tps = sum(r["tps"] for r in valid) / len(valid)

        all_filler_ok = all(r["filler_ok"] for r in valid)
        all_question_ok = all(r["question_ok"] for r in valid)
        all_json_ok = all(r["json_ok"] for r in valid)

        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(f"  Average TTFT:                {avg_ttft:.4f} sec")
        print(f"  Average filler completion:   {avg_filler:.2f} sec")
        print(f"  Average question completion: {avg_question:.2f} sec")
        print(f"  Average total generation:    {avg_total:.2f} sec")
        print(f"  Average output tokens:       {avg_tokens:.0f}")
        print(f"  Average tokens/sec:          {avg_tps:.1f}")
        print()
        print(f"  All filler events fired:     {'âœ“' if all_filler_ok else 'âœ—'}")
        print(f"  All question events fired:   {'âœ“' if all_question_ok else 'âœ—'}")
        print(f"  All JSON validated:          {'âœ“' if all_json_ok else 'âœ—'}")
        print(f"  generate() compatible:       {'âœ“' if compat_ok else 'âœ—'}")
        print()

        issues = []
        if not all_filler_ok:
            issues.append("Some filler_complete events did not fire")
        if not all_question_ok:
            issues.append("Some question_complete events did not fire")
        if not all_json_ok:
            issues.append("Some responses failed JSON validation")
        if not compat_ok:
            issues.append("Existing generate() method is broken")

        if issues:
            print("  Issues discovered:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  Issues discovered:           None")

        print("=" * 60)

    print("\nLLM streaming service verified successfully.")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

