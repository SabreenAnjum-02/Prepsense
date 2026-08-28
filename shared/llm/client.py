import json
import logging
import asyncio
# Need to gracefully handle lack of aiohttp in this minimal mock setup, but ideally this is used
try:
    import aiohttp
except ImportError:
    aiohttp = None

from typing import Dict, Any, Optional, Callable, Awaitable
from .models import LLMRequest, LLMResponse, LLMStreamEvent
from .exceptions import LLMConnectionError, LLMTimeoutError, LLMFormatError
from shared.error_handler import with_retry
from shared.config import config

logger = logging.getLogger(__name__)


class _JsonStringExtractor:
    """Incremental state machine that safely extracts completed JSON string
    values from a growing text buffer.

    Handles escaped quotes, escaped backslashes, and unicode escapes
    correctly. Does NOT attempt to parse full JSON — it only tracks
    whether we are inside a JSON string value and when that string closes.
    """

    # States
    SCANNING = 0       # Outside any string, looking for a key
    IN_KEY = 1         # Inside a JSON key string
    AFTER_KEY = 2      # Seen closing quote of key, expecting ':'
    EXPECT_VALUE = 3   # Seen ':', expecting value start
    IN_STRING_VALUE = 4  # Inside a JSON string value
    AFTER_VALUE = 5    # Completed a value, expecting ',' or '}'

    def __init__(self):
        self._state = self.SCANNING
        self._escape_next = False
        self._current_key = ""
        self._current_value = ""
        self._completed: dict = {}  # key -> value for completed string pairs
        self._depth = 0  # brace depth

    @property
    def completed_keys(self) -> dict:
        """Returns a dict of all completed key-value string pairs so far."""
        return dict(self._completed)

    def feed(self, text: str) -> list:
        """Feed new text and return a list of (key, value) pairs that
        became complete during this feed call."""
        newly_completed = []

        for ch in text:
            if self._escape_next:
                # Previous char was backslash inside a string
                if self._state == self.IN_KEY:
                    self._current_key += ch
                elif self._state == self.IN_STRING_VALUE:
                    self._current_value += ch
                self._escape_next = False
                continue

            if self._state == self.SCANNING:
                if ch == '"':
                    self._state = self.IN_KEY
                    self._current_key = ""
                elif ch == '{':
                    self._depth += 1
                elif ch == '}':
                    self._depth -= 1

            elif self._state == self.IN_KEY:
                if ch == '\\':
                    self._escape_next = True
                    self._current_key += ch
                elif ch == '"':
                    # Key string closed
                    self._state = self.AFTER_KEY
                else:
                    self._current_key += ch

            elif self._state == self.AFTER_KEY:
                if ch == ':':
                    self._state = self.EXPECT_VALUE

            elif self._state == self.EXPECT_VALUE:
                if ch == '"':
                    self._state = self.IN_STRING_VALUE
                    self._current_value = ""
                elif ch in ' \t\n\r':
                    continue  # skip whitespace before value
                else:
                    # Non-string value (number, bool, null, array, object)
                    # We don't track these — reset to scanning
                    self._state = self.SCANNING

            elif self._state == self.IN_STRING_VALUE:
                if ch == '\\':
                    self._escape_next = True
                    self._current_value += ch
                elif ch == '"':
                    # Value string closed — record it
                    # Unescape the value for consumer use
                    clean_value = self._current_value.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
                    self._completed[self._current_key] = clean_value
                    newly_completed.append((self._current_key, clean_value))
                    self._state = self.AFTER_VALUE
                else:
                    self._current_value += ch

            elif self._state == self.AFTER_VALUE:
                if ch == ',':
                    self._state = self.SCANNING
                elif ch == '}':
                    self._depth -= 1
                    self._state = self.SCANNING

        return newly_completed


class OllamaClient:
    """Asynchronous client for interacting with a local Ollama LLM instance."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = config.model.model_name
        self._ensure_aiohttp()

    def _ensure_aiohttp(self):
        if aiohttp is None:
            logger.warning("aiohttp is not installed. OllamaClient will fail if actually invoked.")

    @with_retry(max_retries=3, delay=1.0)
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Send a generation request to the LLM.
        Automatically retries on timeout or transient connection errors.
        """
        import time
        t_start = time.perf_counter()
        
        from api.config import DEV_MODE
        if DEV_MODE:
            logger.info("DEV_MODE: Returning stub LLM response.")
            stub_json = {"conversational_filler": "Let's begin.", "question": "Can you describe a technical system you designed and built?"}
            return LLMResponse(
                raw_text=json.dumps(stub_json),
                parsed_json=stub_json,
                metadata={"prep_latency": 0.001, "gen_latency": 0.001, "parse_latency": 0.001}
            )

        if aiohttp is None:
            raise LLMConnectionError("aiohttp is required to connect to Ollama.")

        url = f"{self.base_url}/api/generate"
        
        options = {
            "temperature": request.temperature
        }
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "stream": False,
            "options": options
        }
        
        if request.system_prompt:
            payload["system"] = request.system_prompt
            
        if request.require_json:
            payload["format"] = "json"
            
        logger.info(f"OllamaClient: Sending request to model '{self.model}'")
        
        t_prep_done = time.perf_counter()
        prep_latency = t_prep_done - t_start
        
        try:
            async with aiohttp.ClientSession() as session:
                # 120 second timeout to allow local model to load into memory
                async with session.post(url, json=payload, timeout=120) as response:
                    if response.status != 200:
                        raise LLMConnectionError(f"Ollama returned HTTP status {response.status}")
                        
                    t_gen_done = time.perf_counter()
                    gen_latency = t_gen_done - t_prep_done
                    
                    data = await response.json()
                    raw_text = data.get("response", "")
                    
                    parsed_json = None
                    if request.require_json:
                        try:
                            # Sometimes models still wrap json in markdown block
                            clean_text = raw_text.strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                            
                            parsed_json = json.loads(clean_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"OllamaClient: Failed to parse JSON response")
                            raise LLMFormatError(f"Invalid JSON returned from model: {e}")
                            
                    t_parse_done = time.perf_counter()
                    parse_latency = t_parse_done - t_gen_done
                    total_latency = t_parse_done - t_start
                    
                    logger.info(f"[LLM_BREAKDOWN] preparation={prep_latency:.4f}s generation={gen_latency:.4f}s parsing={parse_latency:.4f}s total={total_latency:.4f}s")
                            
                    return LLMResponse(
                        raw_text=raw_text,
                        parsed_json=parsed_json,
                        metadata={
                            "eval_count": data.get("eval_count", 0),
                            "prompt_eval_count": data.get("prompt_eval_count", 0),
                            "eval_duration": data.get("eval_duration", 0),
                            "prompt_eval_duration": data.get("prompt_eval_duration", 0),
                            "total_duration": data.get("total_duration", 0),
                            "prep_latency": prep_latency,
                            "gen_latency": gen_latency,
                            "parse_latency": parse_latency
                        }
                    )
        except asyncio.TimeoutError:
            raise LLMTimeoutError("Ollama request timed out.")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}")

    @with_retry(max_retries=3, delay=1.0)
    async def generate_stream(
        self,
        request: LLMRequest,
        on_event: Optional[Callable[[LLMStreamEvent], Awaitable[None]]] = None
    ) -> LLMResponse:
        """Stream a generation request from Ollama, emitting milestone events.

        Sends ``stream=true`` to Ollama and reads newline-delimited JSON
        chunks.  As tokens arrive the accumulated text is fed through a
        safe incremental JSON-string extractor which detects when
        ``conversational_filler`` and ``question`` values are complete.

        Args:
            request: The LLM request (same model used by generate()).
            on_event: Optional async callback invoked for each
                      LLMStreamEvent milestone (filler_complete,
                      question_complete, stream_complete).

        Returns:
            A fully validated LLMResponse identical in shape to what
            generate() returns, so callers can swap transparently.
        """
        import time
        t_start = time.perf_counter()

        from api.config import DEV_MODE
        if DEV_MODE:
            logger.info("DEV_MODE: Returning stub LLM stream response.")
            stub_json = {"conversational_filler": "Let's begin.", "question": "Can you walk me through a technical system you designed and built?"}
            return LLMResponse(
                raw_text=json.dumps(stub_json),
                parsed_json=stub_json,
                metadata={"prep_latency": 0.001, "gen_latency": 0.001, "parse_latency": 0.001}
            )

        if aiohttp is None:
            raise LLMConnectionError("aiohttp is required to connect to Ollama.")

        url = f"{self.base_url}/api/generate"

        options = {
            "temperature": request.temperature
        }
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "stream": True,
            "options": options
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt

        if request.require_json:
            payload["format"] = "json"

        logger.info(f"[LLM_STREAM] stream started — model '{self.model}'")

        t_start = time.perf_counter()
        accumulated_text = ""
        token_count = 0
        t_first_token = None
        t_filler_complete = None
        t_question_complete = None

        extractor = _JsonStringExtractor()
        final_meta: Dict[str, Any] = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload,
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status != 200:
                        raise LLMConnectionError(
                            f"Ollama returned HTTP status {response.status}"
                        )

                    async for line in response.content:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        token_text = chunk.get("response", "")
                        accumulated_text += token_text
                        token_count += 1

                        # Record TTFT
                        if token_count == 1:
                            t_first_token = time.perf_counter() - t_start
                            logger.info(
                                f"[LLM_STREAM] first token received: "
                                f"{t_first_token:.4f} sec"
                            )

                        # Feed extractor to detect completed JSON string values
                        newly_completed = extractor.feed(token_text)
                        for key, value in newly_completed:
                            if key == "conversational_filler" and t_filler_complete is None:
                                t_filler_complete = time.perf_counter() - t_start
                                logger.info(
                                    f"[LLM_STREAM] filler complete: "
                                    f"{t_filler_complete:.2f} sec"
                                )
                                if on_event:
                                    await on_event(LLMStreamEvent(
                                        event_type="filler_complete",
                                        text=value,
                                        accumulated_text=accumulated_text,
                                        is_complete=False
                                    ))

                            elif key == "question" and t_question_complete is None:
                                t_question_complete = time.perf_counter() - t_start
                                logger.info(
                                    f"[LLM_STREAM] question complete: "
                                    f"{t_question_complete:.2f} sec"
                                )
                                if on_event:
                                    await on_event(LLMStreamEvent(
                                        event_type="question_complete",
                                        text=value,
                                        accumulated_text=accumulated_text,
                                        is_complete=False
                                    ))

                        # Check for stream end
                        if chunk.get("done", False):
                            final_meta = {
                                "eval_count": chunk.get("eval_count", token_count),
                                "prompt_eval_count": chunk.get("prompt_eval_count", 0),
                                "eval_duration": chunk.get("eval_duration", 0),
                                "prompt_eval_duration": chunk.get("prompt_eval_duration", 0),
                                "total_duration": chunk.get("total_duration", 0),
                            }
                            break

        except asyncio.TimeoutError:
            raise LLMTimeoutError("Ollama streaming request timed out.")
        except aiohttp.ClientError as e:
            raise LLMConnectionError(
                f"Failed to connect to Ollama during streaming: {e}"
            )

        t_total = time.perf_counter() - t_start
        logger.info(f"[LLM_STREAM] stream completed: {t_total:.2f} sec")

        # --- Final JSON validation ---
        parsed_json = None
        if request.require_json:
            try:
                clean_text = accumulated_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                parsed_json = json.loads(clean_text)
            except json.JSONDecodeError as e:
                logger.error(f"[LLM_STREAM] Final JSON validation failed: {e}")
                raise LLMFormatError(
                    f"Invalid JSON from streamed response: {e}"
                )

        # Compute tokens/sec from Ollama metadata
        eval_dur_sec = final_meta.get("eval_duration", 0) / 1e9
        eval_count = final_meta.get("eval_count", token_count)
        tokens_per_sec = (eval_count / eval_dur_sec) if eval_dur_sec > 0 else 0.0

        ttft_str = f"{t_first_token:.4f}s" if t_first_token else "N/A"
        filler_str = f"{t_filler_complete:.2f}s" if t_filler_complete else "N/A"
        question_str = f"{t_question_complete:.2f}s" if t_question_complete else "N/A"

        logger.info(
            f"[LLM_STREAM] tokens={eval_count} "
            f"prompt_tokens={final_meta.get('prompt_eval_count', 0)} "
            f"tps={tokens_per_sec:.1f} "
            f"ttft={ttft_str} "
            f"filler={filler_str} "
            f"question={question_str} "
            f"total={t_total:.2f}s"
        )

        # Attach timing info to metadata
        final_meta.update({
            "stream": True,
            "ttft": t_first_token,
            "t_filler_complete": t_filler_complete,
            "t_question_complete": t_question_complete,
            "t_total": t_total,
            "tokens_per_sec": tokens_per_sec,
            "prep_latency": 0.0,
            "gen_latency": t_total,
            "parse_latency": 0.0,
        })

        llm_response = LLMResponse(
            raw_text=accumulated_text,
            parsed_json=parsed_json,
            metadata=final_meta
        )

        # Emit final completion event
        if on_event:
            await on_event(LLMStreamEvent(
                event_type="stream_complete",
                text=accumulated_text,
                accumulated_text=accumulated_text,
                is_complete=True
            ))

        return llm_response
