from typing import List, Dict, Any
from .models import EvaluationPrediction, BenchmarkSummary


class BenchmarkMetricsCalculator:
    """Calculates statistical metrics, error distributions, and qualitative evaluator weaknesses."""

    @staticmethod
    def calculate_summary(predictions: List[EvaluationPrediction]) -> BenchmarkSummary:
        if not predictions:
            return BenchmarkSummary(
                total_cases=0,
                total_evaluations=0,
                passed_evaluations=0,
                failed_evaluations=0,
                mae=0.0,
                accuracy_pm1=0.0,
                accuracy_pm2=0.0,
                accuracy_pm10=0.0,
                accuracy_pm20=0.0,
                expected_average_score=0.0,
                predicted_average_score=0.0,
                largest_errors=[],
                identified_weaknesses=[]
            )

        total_evals = len(predictions)
        
        # Determine case count
        unique_cases = len(set(p.case_id for p in predictions))
        
        # Calculate MAE
        total_abs_error = sum(p.absolute_error for p in predictions)
        mae = total_abs_error / total_evals

        # Accuracies
        pm1_count = sum(1 for p in predictions if p.is_pass_pm1)
        pm2_count = sum(1 for p in predictions if p.is_pass_pm2)
        pm10_count = sum(1 for p in predictions if p.is_pass_pm10)
        pm20_count = sum(1 for p in predictions if p.is_pass_pm20)

        acc_pm1 = (pm1_count / total_evals) * 100.0
        acc_pm2 = (pm2_count / total_evals) * 100.0
        acc_pm10 = (pm10_count / total_evals) * 100.0
        acc_pm20 = (pm20_count / total_evals) * 100.0

        # Averages
        expected_avg = sum(p.expected_score for p in predictions) / total_evals
        predicted_avg = sum(p.predicted_score for p in predictions) / total_evals

        # Pass / Fail criteria (Pass if prediction is within +-15 points of expected score)
        passed = sum(1 for p in predictions if p.absolute_error <= 15.0 and p.error_message is None)
        failed = total_evals - passed

        # Largest errors (top 5 worst predictions)
        sorted_errors = sorted(predictions, key=lambda p: p.absolute_error, reverse=True)
        largest_errors = sorted_errors[:5]

        # Identify systematic weaknesses
        weaknesses = BenchmarkMetricsCalculator._identify_weaknesses(predictions)

        return BenchmarkSummary(
            total_cases=unique_cases,
            total_evaluations=total_evals,
            passed_evaluations=passed,
            failed_evaluations=failed,
            mae=round(mae, 2),
            accuracy_pm1=round(acc_pm1, 1),
            accuracy_pm2=round(acc_pm2, 1),
            accuracy_pm10=round(acc_pm10, 1),
            accuracy_pm20=round(acc_pm20, 1),
            expected_average_score=round(expected_avg, 2),
            predicted_average_score=round(predicted_avg, 2),
            largest_errors=largest_errors,
            identified_weaknesses=weaknesses
        )

    @staticmethod
    def _identify_weaknesses(predictions: List[EvaluationPrediction]) -> List[str]:
        weaknesses = []

        # 1. Over-scoring weak/incorrect answers
        weak_incorrect_preds = [p for p in predictions if p.quality_level in ["weak", "incorrect"]]
        if weak_incorrect_preds:
            avg_over = sum(p.error_delta for p in weak_incorrect_preds) / len(weak_incorrect_preds)
            if avg_over > 10.0:
                weaknesses.append(
                    f"Over-scoring low-quality answers: Weak/Incorrect answers scored an average of {avg_over:+.1f} points higher than expected."
                )

        # 2. Under-scoring excellent answers
        excellent_preds = [p for p in predictions if p.quality_level == "excellent"]
        if excellent_preds:
            avg_under = sum(p.error_delta for p in excellent_preds) / len(excellent_preds)
            if avg_under < -10.0:
                weaknesses.append(
                    f"Under-scoring high-quality answers: Excellent answers scored an average of {avg_under:+.1f} points lower than expected."
                )

        # 3. Compression / Central tendency bias (all scores clumped around 50-70)
        score_range = max(p.predicted_score for p in predictions) - min(p.predicted_score for p in predictions) if predictions else 0
        if score_range < 40.0:
            weaknesses.append(
                f"Score Compression Bias: Evaluator predictions range only {score_range:.1f} points, failing to distinguish severe quality differences."
            )

        # 4. Topic-specific performance gaps
        topics = set(p.topic for p in predictions)
        for t in topics:
            t_preds = [p for p in predictions if p.topic == t]
            t_mae = sum(p.absolute_error for p in t_preds) / len(t_preds)
            if t_mae > 20.0:
                weaknesses.append(
                    f"Topic Inaccuracy ({t}): High MAE of {t_mae:.1f} points on {t} questions."
                )

        if not weaknesses:
            weaknesses.append("No major systematic evaluation biases detected.")

        return weaknesses
