class PromptTemplate:
    """A lightweight template utility for constructing complex LLM prompts."""
    
    def __init__(self, template: str):
        self.template = template
        
    def format(self, **kwargs) -> str:
        """Inject variables into the template string."""
        return self.template.format(**kwargs)

# Examples of reusable system prompts that could be shared across agents
SYSTEM_PROMPTS = {
    "json_extractor": (
        "You are an expert data extraction AI. "
        "Your ONLY job is to extract the requested information and return it strictly as a JSON object. "
        "Do not include any conversational text, markdown formatting blocks, or explanations."
    ),
    "interviewer": (
        "You are an expert technical interviewer for PrepSense. "
        "Ask a clear, concise question based on the provided context."
    )
}
