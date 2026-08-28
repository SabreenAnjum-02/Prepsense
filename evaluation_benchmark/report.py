from typing import List
from .models import EvaluationPrediction, BenchmarkSummary


class BenchmarkReporter:
    """Formats and prints comprehensive evaluation benchmark reports."""

    @staticmethod
    def print_report(summary: BenchmarkSummary, predictions: List[EvaluationPrediction]) -> None:
        print("\n" + "=" * 70)
        print("PREPSENSE EVALUATION BENCHMARK REPORT")
        print("=" * 70)
        print(f"Total Benchmark Cases:        {summary.total_cases}")
        print(f"Total Answer Evaluations:     {summary.total_evaluations}")
        print(f"Passed Evaluations (±15 pts): {summary.passed_evaluations} / {summary.total_evaluations} ({summary.passed_evaluations/summary.total_evaluations*100:.1f}%)")
        print(f"Failed Evaluations:           {summary.failed_evaluations}")
        print("----------------------------------------------------------------------")
        print(f"Mean Absolute Error (MAE):    {summary.mae:.2f} points (out of 100)")
        print(f"Accuracy within ±1 point:     {summary.accuracy_pm1:.1f}%")
        print(f"Accuracy within ±2 points:    {summary.accuracy_pm2:.1f}%")
        print(f"Accuracy within ±10 points:   {summary.accuracy_pm10:.1f}%  (±1 on 10-pt scale)")
        print(f"Accuracy within ±20 points:   {summary.accuracy_pm20:.1f}%  (±2 on 10-pt scale)")
        print("----------------------------------------------------------------------")
        print(f"Expected Average Score:       {summary.expected_average_score:.2f}")
        print(f"Predicted Average Score:      {summary.predicted_average_score:.2f}")
        print(f"Global Scoring Bias (Delta):  {summary.predicted_average_score - summary.expected_average_score:+.2f} points")
        print("================================================================------")

        # Per-Case Breakdown
        print("\nPER-CASE EVALUATION RESULTS:")
        print("-" * 70)
        print(f"{'Topic':<18} | {'Quality':<10} | {'Expected':<8} | {'Predicted':<9} | {'Error':<7} | {'Status'}")
        print("-" * 70)
        for p in predictions:
            status = "PASS" if p.absolute_error <= 15.0 else "FAIL"
            print(f"{p.topic[:18]:<18} | {p.quality_level:<10} | {p.expected_score:<8.1f} | {p.predicted_score:<9.1f} | {p.error_delta:<+7.1f} | {status}")

        # Largest Scoring Outliers
        print("\n" + "=" * 70)
        print("LARGEST EVALUATION ERRORS (TOP OUTLIERS)")
        print("=" * 70)
        for idx, err in enumerate(summary.largest_errors, 1):
            print(f"{idx}. [{err.topic}] Tier: {err.quality_level.upper()}")
            print(f"   Question: {err.question[:70]}...")
            print(f"   Answer:   {err.candidate_answer[:80]}...")
            print(f"   Expected: {err.expected_score:.1f} | Predicted: {err.predicted_score:.1f} | Error: {err.error_delta:+.1f} pts (Abs: {err.absolute_error:.1f})")
            print()

        # Evaluator Weaknesses
        print("=" * 70)
        print("IDENTIFIED EVALUATOR WEAKNESSES")
        print("=" * 70)
        for idx, w in enumerate(summary.identified_weaknesses, 1):
            print(f"{idx}. {w}")
        print("=" * 70 + "\n")
