from typing import List, Tuple, Optional, Dict, Any
from agents.shared.types import CriterionEvaluation
from .utils import get_logger

logger = get_logger(__name__)


class ScoringEngine:
    """Calculates application-side deterministic weighted scores from extracted criterion evidence.
    
    The LLM provides per-dimension scores as an informed baseline.
    The ScoringEngine validates, adjusts, and caps those scores based on
    extracted evidence (observed, missing, incorrect) to prevent generosity bias
    while preserving nuanced partial credit.
    """

    def calculate_6d_scores_from_evidence(
        self,
        criterion_evaluations: List[CriterionEvaluation],
        role_weighting: Optional[dict] = None,
        practical_evaluation: Optional[Any] = None
    ) -> dict:
        """Calculates evidence-grounded scores across the 6 dimensions:
        1. technical_score (0-100)
        2. practical_score (0-100)
        3. problem_solving_score (0-100)
        4. communication_score (0-100)
        5. behavioral_score (0-100)
        6. role_fit_score (0-100)
        plus confidence_score and overall_score.
        """
        logger.info("ScoringEngine: Calculating 6-dimensional scores from evidence.")

        tech_crit = next((c for c in criterion_evaluations if "technical" in c.criterion_name.lower()), None)
        comp_crit = next((c for c in criterion_evaluations if "completeness" in c.criterion_name.lower() or "coverage" in c.criterion_name.lower() or "practical" in c.criterion_name.lower()), None)
        reas_crit = next((c for c in criterion_evaluations if "reasoning" in c.criterion_name.lower() or "problem" in c.criterion_name.lower()), None)
        comm_crit = next((c for c in criterion_evaluations if "communication" in c.criterion_name.lower()), None)
        behav_crit = next((c for c in criterion_evaluations if "behavioral" in c.criterion_name.lower() or "leadership" in c.criterion_name.lower() or "team" in c.criterion_name.lower()), None)
        role_crit = next((c for c in criterion_evaluations if "role" in c.criterion_name.lower() or "fit" in c.criterion_name.lower()), None)

        # 1. Technical Knowledge Score
        tech_score = self._score_technical(tech_crit, criterion_evaluations)

        # 2. Practical / Domain Execution Score
        prac_score = self._score_practical(comp_crit, default=tech_score)

        # 3. Problem Solving & Analytical Reasoning Score
        prob_score = self._score_reasoning(reas_crit, default=tech_score)

        # Ground Practical and Problem Solving in actual Sandbox Execution if available
        if practical_evaluation:
            prac_exec_score = getattr(practical_evaluation, "overall_practical_score", 75.0)
            tests_passed = getattr(practical_evaluation, "tests_passed", 0)
            total_tests = getattr(practical_evaluation, "total_tests", 0)

            # Failure penalty / anti-inflation check
            if total_tests > 0 and tests_passed == 0:
                prac_score = min(25.0, prac_exec_score)
                prob_score = min(prob_score, 45.0)
            else:
                prac_score = (prac_score * 0.35) + (prac_exec_score * 0.65)
                comp_score = getattr(practical_evaluation, "complexity_score", 75.0)
                prob_score = (prob_score * 0.60) + (comp_score * 0.40)

        # 4. Communication Score
        comm_score = self._score_communication(comm_crit, tech_score)

        # 5. Behavioral Performance Score
        behav_score = self._score_behavioral(behav_crit, default=comm_score)

        # 6. Role Fit Score
        role_fit_score = self._score_role_fit(role_crit, tech_score, prac_score)

        # Confidence Score
        conf_score = self._calculate_confidence_score(criterion_evaluations)

        # Default weights if not specified by role blueprint
        weights = role_weighting or {
            "technical": 0.30,
            "practical": 0.25,
            "problem_solving": 0.20,
            "communication": 0.10,
            "behavioral": 0.10,
            "role_fit": 0.05
        }

        raw_overall = (
            (tech_score * weights.get("technical", 0.30)) +
            (prac_score * weights.get("practical", 0.25)) +
            (prob_score * weights.get("problem_solving", 0.20)) +
            (comm_score * weights.get("communication", 0.10)) +
            (behav_score * weights.get("behavioral", 0.10)) +
            (role_fit_score * weights.get("role_fit", 0.05))
        )

        if tech_score < 30.0:
            overall_score = min(raw_overall, tech_score + 15.0)
        else:
            overall_score = raw_overall

        res = {
            "technical_score": round(max(0.0, min(100.0, tech_score)), 1),
            "practical_score": round(max(0.0, min(100.0, prac_score)), 1),
            "problem_solving_score": round(max(0.0, min(100.0, prob_score)), 1),
            "communication_score": round(max(0.0, min(100.0, comm_score)), 1),
            "behavioral_score": round(max(0.0, min(100.0, behav_score)), 1),
            "role_fit_score": round(max(0.0, min(100.0, role_fit_score)), 1),
            "confidence_score": round(max(0.0, min(100.0, conf_score)), 1),
            "overall_score": round(max(0.0, min(100.0, overall_score)), 1),
        }
        logger.info(f"ScoringEngine 6D Result -> {res}")
        return res

    def calculate_scores_from_evidence(
        self,
        criterion_evaluations: List[CriterionEvaluation]
    ) -> Tuple[float, float, float, float, float]:
        """Backward-compatible method returning (tech, comm, reas, conf, overall)."""
        d = self.calculate_6d_scores_from_evidence(criterion_evaluations)
        return (
            d["technical_score"],
            d["communication_score"],
            d["problem_solving_score"],
            d["confidence_score"],
            d["overall_score"]
        )

    def _score_technical(self, tech_crit: CriterionEvaluation, all_crits: List[CriterionEvaluation]) -> float:
        """Score technical correctness using LLM score + evidence validation."""
        # Collect ALL incorrect evidence across all criteria
        all_incorrect = []
        for c in all_crits:
            all_incorrect.extend(c.incorrect_evidence)

        if all_incorrect:
            logger.warning(f"ScoringEngine: Detected {len(all_incorrect)} factually incorrect statements: {all_incorrect}")
            # Determine if candidate also demonstrated SOME correct knowledge
            n_obs = len(tech_crit.observed_evidence) if tech_crit else 0
            has_partial_credit = n_obs > 0

            if len(all_incorrect) >= 2:
                # Multiple false claims
                if has_partial_credit:
                    # Partial misconception — some correct knowledge exists
                    return min(tech_crit.score if tech_crit and tech_crit.score > 0.0 else 25.0, 30.0)
                else:
                    # Total fabrication — no correct knowledge at all
                    return 10.0
            else:
                # Single false claim
                if has_partial_credit:
                    return min(tech_crit.score if tech_crit and tech_crit.score > 0.0 else 30.0, 35.0)
                else:
                    return 15.0

        if not tech_crit:
            return 50.0

        llm_score = tech_crit.score if tech_crit.score is not None else 50.0
        n_obs = len(tech_crit.observed_evidence)
        n_miss = len(tech_crit.missing_evidence)

        # No evidence extracted at all — LLM returned score directly
        if n_obs == 0 and n_miss == 0:
            return llm_score

        # No observed evidence + missing topics = failed/blank answer
        if n_obs == 0 and n_miss > 0:
            # If candidate gave no correct evidence, score should be the low LLM score (e.g. 0-15)
            return min(llm_score, 15.0) if llm_score <= 15.0 else min(llm_score, 25.0)

        # Trust LLM score but apply evidence-based guardrails
        # If LLM scored high but evidence shows missing topics, cap proportionally
        if n_obs > 0 and n_miss > 0:
            coverage_ratio = n_obs / (n_obs + n_miss)
            evidence_ceiling = 40.0 + (coverage_ratio * 55.0)  # 40 to 95
            return min(llm_score, evidence_ceiling)

        # Observed evidence with nothing missing — trust the LLM score
        if n_obs > 0 and n_miss == 0:
            return max(llm_score, 85.0)

        return llm_score

    def _score_completeness(self, comp_crit: CriterionEvaluation, default: float) -> float:
        """Score completeness using LLM score + missing evidence count."""
        if not comp_crit:
            return default

        llm_score = comp_crit.score if comp_crit.score is not None else default
        n_obs = len(comp_crit.observed_evidence)
        n_miss = len(comp_crit.missing_evidence)

        # No evidence extracted — trust LLM score
        if n_obs == 0 and n_miss == 0:
            return llm_score

        if n_obs == 0 and n_miss > 0:
            return min(llm_score, 15.0) if llm_score <= 15.0 else min(llm_score, 25.0)

        if n_obs > 0 and n_miss > 0:
            coverage_ratio = n_obs / (n_obs + n_miss)
            evidence_ceiling = 35.0 + (coverage_ratio * 60.0)  # 35 to 95
            return min(llm_score, evidence_ceiling)

        if n_obs > 0 and n_miss == 0:
            return max(llm_score, 80.0)

        return llm_score

    def _score_reasoning(self, reas_crit: CriterionEvaluation, default: float) -> float:
        """Score reasoning using LLM score + evidence."""
        if not reas_crit:
            return default

        llm_score = reas_crit.score if reas_crit.score is not None else default
        n_obs = len(reas_crit.observed_evidence)
        n_miss = len(reas_crit.missing_evidence)
        n_inc = len(reas_crit.incorrect_evidence)

        # If incorrect evidence propagated to reasoning, cap severely
        if n_inc > 0:
            return min(llm_score, 20.0)

        if n_obs == 0 and n_miss > 0:
            return min(llm_score, 15.0) if llm_score <= 15.0 else min(llm_score, 25.0)

        return llm_score

    def _score_communication(self, comm_crit: CriterionEvaluation, tech_score: float) -> float:
        """Score communication — must not inflate technically incorrect answers."""
        if not comm_crit:
            base = 60.0
        else:
            base = comm_crit.score if comm_crit.score is not None else 60.0

        # Communication cap when technical correctness is very poor
        if tech_score <= 15.0:
            return min(base, 50.0)
        elif tech_score < 30.0:
            return min(base, 60.0)

        return base

    def _score_practical(self, prac_crit: Optional[CriterionEvaluation], default: float) -> float:
        """Score practical and implementation skills based on concrete evidence."""
        if not prac_crit:
            return default

        llm_score = prac_crit.score if prac_crit.score is not None else default
        n_obs = len(prac_crit.observed_evidence)
        n_miss = len(prac_crit.missing_evidence)
        n_inc = len(prac_crit.incorrect_evidence)

        if n_inc > 0:
            return min(llm_score, 25.0)

        if n_obs == 0 and n_miss > 0:
            return min(llm_score, 15.0)

        if n_obs > 0 and n_miss > 0:
            ratio = n_obs / (n_obs + n_miss)
            return min(llm_score, 35.0 + (ratio * 60.0))

        if n_obs > 0 and n_miss == 0:
            return max(llm_score, 85.0)

        return llm_score

    def _score_behavioral(self, behav_crit: Optional[CriterionEvaluation], default: float) -> float:
        """Score behavioral performance and situational clarity."""
        if not behav_crit:
            return default

        llm_score = behav_crit.score if behav_crit.score is not None else default
        n_obs = len(behav_crit.observed_evidence)
        n_miss = len(behav_crit.missing_evidence)

        if n_obs == 0 and n_miss > 0:
            return min(llm_score, 30.0)

        return llm_score

    def _score_role_fit(self, role_crit: Optional[CriterionEvaluation], tech_score: float, prac_score: float) -> float:
        """Score role readiness and alignment with role expectations."""
        if not role_crit:
            # Baseline derived from technical and practical execution
            return (tech_score * 0.6) + (prac_score * 0.4)

        llm_score = role_crit.score if role_crit.score is not None else 60.0
        return llm_score

    def _calculate_confidence_score(self, evaluations: List[CriterionEvaluation]) -> float:
        if not evaluations:
            return 70.0

        conf_map = {"HIGH": 90.0, "MEDIUM": 70.0, "LOW": 40.0}
        scores = [conf_map.get(c.confidence.upper(), 70.0) for c in evaluations]
        return sum(scores) / len(scores)
