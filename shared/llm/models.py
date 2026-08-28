from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class LLMRequest(BaseModel):
    """Encapsulates a standard prompt request to the LLM."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    require_json: bool = False
    max_tokens: Optional[int] = None

class LLMResponse(BaseModel):
    """Encapsulates the response from the LLM, optionally including parsed JSON."""
    raw_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMStreamEvent(BaseModel):
    """Represents an incremental event during LLM streaming generation.

    Emitted by generate_stream() to notify callers of meaningful
    milestones without exposing raw transport details.
    """
    event_type: str = Field(
        ...,
        description="One of: 'token', 'filler_complete', 'question_complete', 'stream_complete', 'error'"
    )
    text: str = Field(
        default="",
        description="The text payload for this event (e.g. the filler text, the question text, or a single token)"
    )
    accumulated_text: str = Field(
        default="",
        description="The full accumulated raw text up to this point in the stream"
    )
    is_complete: bool = Field(
        default=False,
        description="True only when the entire stream has finished and the response is validated"
    )

