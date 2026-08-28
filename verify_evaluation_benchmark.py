import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY_BENCHMARK")

from evaluation_benchmark import (
    get_benchmark_dataset,
    BenchmarkRunner,
    BenchmarkMetricsCalculator,
    BenchmarkReporter
)


async def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logger.info("Initializing Evaluation Benchmark Framework...")
    
    # Load dataset
    import os
    cases = get_benchmark_dataset()
    max_cases_env = os.getenv("PREPSENSE_BENCHMARK_MAX_CASES")
    if max_cases_env and max_cases_env.isdigit():
        max_cases = int(max_cases_env)
        cases = cases[:max_cases]
    logger.info(f"Loaded {len(cases)} benchmark cases covering {len(set(c.topic for c in cases))} topics.")

    # Initialize runner with real EvaluatorAgent
    runner = BenchmarkRunner()

    logger.info("Executing benchmark evaluations against real EvaluatorAgent...")

    def progress(current: int, total: int, pred):
        logger.info(
            f"[{current}/{total}] Evaluated {pred.topic} ({pred.quality_level}): "
            f"Expected={pred.expected_score:.1f}, Predicted={pred.predicted_score:.1f}, Error={pred.error_delta:+.1f}"
        )

    predictions = await runner.run_benchmark(cases, progress_callback=progress)

    if not predictions:
        logger.error("Benchmark runner produced no predictions. Aborting.")
        sys.exit(1)

    # Compute metrics
    summary = BenchmarkMetricsCalculator.calculate_summary(predictions)

    # Print report
    BenchmarkReporter.print_report(summary, predictions)

    print("\nEvaluation benchmark completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
