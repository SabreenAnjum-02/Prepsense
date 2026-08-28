import json
from typing import Dict, Any, Optional
from agents.shared.types import CandidateProfile
from shared.llm import OllamaClient, LLMRequest, SYSTEM_PROMPTS
from shared.llm.exceptions import LLMFormatError
from shared.error_handler import with_retry
from .utils import get_logger

logger = get_logger(__name__)

class ProfileBuilder:
    """Builds a structured CandidateProfile using the local LLM."""
    
    def __init__(self, llm_client: Optional[OllamaClient] = None):
        self._llm = llm_client or OllamaClient()

    @with_retry(max_retries=2, exceptions=(LLMFormatError,))
    async def build_profile(self, sections: Dict[str, str]) -> CandidateProfile:
        """Construct a structured CandidateProfile using the section data via LLM."""
        logger.info("ProfileBuilder: Asking LLM to extract CandidateProfile from resume sections.")
        
        # We can just dump all sections into the prompt text
        resume_text = "\n\n".join([f"[{k.upper()}]\n{v}" for k, v in sections.items()])
        
        prompt = (
            "Extract the following information from the resume text into a strictly valid JSON object:\n"
            "- name (string)\n"
            "- email (string or null)\n"
            "- phone (string or null)\n"
            "- linkedin (string or null)\n"
            "- github (string or null)\n"
            "- skills (list of strings)\n"
            "- education (list of strings, e.g. 'B.S. Computer Science, University of Technology, 2019')\n"
            "- experience (list of strings, e.g. 'Software Engineer at TechCorp, 2020-Present')\n"
            "- projects (list of strings, e.g. 'AuthSystem - centralized JWT auth')\n"
            "- certifications (list of strings)\n"
            "- achievements (list of strings)\n"
            "- languages (list of strings)\n\n"
            f"RESUME TEXT:\n{resume_text}"
        )
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPTS.get("json_extractor"),
            temperature=0.1,
            require_json=True
        )
        
        response = await self._llm.generate(request)
        
        if not response.parsed_json:
            raise LLMFormatError("LLM returned empty or invalid JSON")
            
        try:
            profile = CandidateProfile(**response.parsed_json)
            return profile
        except Exception as e:
            logger.error(f"ProfileBuilder: LLM JSON failed to map to CandidateProfile: {e}")
            raise LLMFormatError(f"Validation failed: {e}")

    def match_job_description(
        self,
        candidate_profile: CandidateProfile,
        target_role: Optional[str] = None,
        target_jd: Optional[str] = None
    ) -> CandidateProfile:
        """Matches candidate profile against target role and optional Job Description."""
        from agents.shared.roles import detect_role, get_role_blueprint
        
        # 1. Determine optimal RoleArchetype
        role_enum = detect_role(
            target_role_str=target_role,
            jd_text=target_jd,
            profile_skills=candidate_profile.skills,
            profile_experience=candidate_profile.experience
        )
        blueprint = get_role_blueprint(role_enum)
        candidate_profile.target_role = role_enum.value
        candidate_profile.target_jd = target_jd

        # If no JD provided, match against the role blueprint's required competencies
        reference_skills = blueprint.required_competencies
        if target_jd and target_jd.strip():
            low_jd = target_jd.lower()
            jd_skills_found = [s for s in blueprint.required_competencies if any(w.lower() in low_jd for w in s.split())]
            if not jd_skills_found:
                jd_skills_found = blueprint.required_competencies
            reference_skills = jd_skills_found

        # Compute matches and gaps
        cand_skills_low = [s.lower() for s in candidate_profile.skills]
        matches = []
        gaps = []
        for req in reference_skills:
            req_words = req.lower().replace("&", " ").replace("/", " ").split()
            if any(w in " ".join(cand_skills_low) for w in req_words if len(w) > 2):
                matches.append(req)
            else:
                gaps.append(req)

        candidate_profile.skill_matches = matches
        candidate_profile.skill_gaps = gaps
        total_reqs = len(matches) + len(gaps)
        candidate_profile.jd_match_percentage = round((len(matches) / max(total_reqs, 1)) * 100.0, 1)

        logger.info(
            f"ProfileBuilder: Role='{candidate_profile.target_role}', "
            f"JD Match={candidate_profile.jd_match_percentage}% "
            f"(Matches: {len(matches)}, Gaps: {len(gaps)})"
        )
        return candidate_profile
