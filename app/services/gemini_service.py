import logging
import os
import random
import time
from typing import Any, Type, TypeVar
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

load_dotenv()

# Configure structured logging
logger = logging.getLogger("interviewiq.gemini")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [GeminiService] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Default models
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS_ENV = os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.5-flash")
FALLBACK_MODELS = [m.strip() for m in FALLBACK_MODELS_ENV.split(",") if m.strip()]
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")

# Default HTTP request timeout in milliseconds (25 seconds)
REQUEST_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "25000"))

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Custom Exceptions for Granular Error Categorization
# ---------------------------------------------------------------------------
class GeminiError(Exception):
    """Base class for Gemini service exceptions."""
    def __init__(self, message: str, status_code: int = 500, category: str = "internal"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.category = category


class GeminiAuthError(GeminiError):
    """Raised when the API key is missing, invalid, or unauthorized."""
    def __init__(self, message: str = "Invalid or missing GEMINI_API_KEY. Please check your credentials."):
        super().__init__(message, status_code=401, category="authentication")


class GeminiQuotaError(GeminiError):
    """Raised when API quota or rate limits are exhausted."""
    def __init__(self, message: str = "Gemini API rate limit or quota exceeded. Please wait a moment."):
        super().__init__(message, status_code=429, category="quota")


class GeminiAvailabilityError(GeminiError):
    """Raised when models are overloaded, unavailable, or 503."""
    def __init__(self, message: str = "Gemini model is temporarily unavailable due to high demand."):
        super().__init__(message, status_code=503, category="availability")


class GeminiTimeoutError(GeminiError):
    """Raised when a request times out."""
    def __init__(self, message: str = "Gemini API request timed out."):
        super().__init__(message, status_code=504, category="timeout")


class GeminiValidationError(GeminiError):
    """Raised when LLM output cannot be validated into expected Pydantic schema."""
    def __init__(self, message: str = "AI response did not conform to the expected structured format."):
        super().__init__(message, status_code=502, category="validation")


# ---------------------------------------------------------------------------
# Centralized Gemini Service
# ---------------------------------------------------------------------------
class GeminiService:
    """
    Centralized, production-hardened Gemini client providing:
    - Safe credential loading from environment
    - Configurable model cascade with automatic fallbacks
    - Bounded exponential backoff retries for transient errors
    - Immediate failure on non-retryable errors (auth, quota)
    - Pydantic structured output parsing with strict bounds validation
    - Enforced request timeouts via types.HttpOptions
    - Connectivity diagnostics & health probes
    - Audio transcription support via multimodal inputs
    """

    def __init__(
        self,
        api_key: str | None = None,
        primary_model: str = PRIMARY_MODEL,
        fallback_models: list[str] | None = None,
        embed_model: str = EMBED_MODEL,
        timeout_ms: int = REQUEST_TIMEOUT_MS,
    ):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    self._api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        self.primary_model = primary_model
        self.fallback_models = fallback_models if fallback_models is not None else FALLBACK_MODELS
        self.embed_model = embed_model
        self.timeout_ms = timeout_ms
        self._client: genai.Client | None = None

    def get_client(self) -> genai.Client:
        """Initialize or retrieve the cached GenAI client with explicit timeout."""
        if self._client is not None:
            return self._client

        if not self._api_key:
            raise GeminiAuthError(
                "GEMINI_API_KEY environment variable is missing. "
                "Set GEMINI_API_KEY in your .env file or deployment environment."
            )

        try:
            self._client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=self.timeout_ms),
            )
            return self._client
        except Exception as exc:
            logger.error("Failed to initialize Google GenAI client: %s", str(exc))
            raise GeminiAuthError(f"Could not initialize Gemini client: {exc}") from exc

    def categorize_exception(self, exc: Exception) -> GeminiError:
        """Categorize raw client/server exceptions into typed domain errors."""
        msg = str(exc)
        err_lower = msg.lower()

        if "api_key" in err_lower or "unauthorized" in err_lower or "401" in err_lower or "403" in err_lower:
            return GeminiAuthError(f"Authentication failed: {msg}")
        if "429" in msg or "resource_exhausted" in err_lower or "quota" in err_lower:
            return GeminiQuotaError("Gemini rate limit or quota exceeded. Please retry after a brief pause.")
        if "503" in msg or "unavailable" in err_lower or "high demand" in err_lower:
            return GeminiAvailabilityError("Gemini service is temporarily experiencing high traffic.")
        if "timed out" in err_lower or "timeout" in err_lower or "504" in msg or "timeouterror" in err_lower:
            return GeminiTimeoutError("Gemini API call timed out.")
        if "404" in msg or "not_found" in err_lower:
            return GeminiAvailabilityError(f"Requested model was not found: {msg}")

        return GeminiError(f"Gemini API request failed: {msg}")

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
        max_retries_per_model: int = 2,
        initial_delay: float = 1.0,
    ) -> T:
        """
        Generate structured data adhering to a Pydantic schema with model cascading and retry backoff.
        """
        client = self.get_client()
        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]

        last_error: Exception | None = None

        for model_name in candidate_models:
            delay = initial_delay
            logger.info("Attempting structured generation with model: %s", model_name)

            for attempt in range(max_retries_per_model):
                try:
                    config = types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=temperature,
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )

                    if response.parsed is not None and isinstance(response.parsed, schema):
                        return response.parsed

                    if response.text:
                        parsed_obj = schema.model_validate_json(response.text)
                        return parsed_obj

                    raise GeminiValidationError("Model returned empty or non-parseable response text.")

                except ValidationError as ve:
                    logger.error("Pydantic validation failure on %s: %s", model_name, str(ve))
                    last_error = GeminiValidationError(f"Response validation failed: {ve}")
                    break

                except (errors.ClientError, errors.ServerError, Exception) as exc:
                    typed_err = self.categorize_exception(exc)
                    last_error = typed_err

                    if isinstance(typed_err, GeminiAuthError):
                        logger.error("Authentication error encountered; aborting immediately: %s", typed_err.message)
                        raise typed_err

                    if isinstance(typed_err, (GeminiQuotaError, GeminiAvailabilityError, GeminiTimeoutError)):
                        if attempt < max_retries_per_model - 1:
                            sleep_sec = delay + random.uniform(0.3, 0.8)
                            logger.warning(
                                "Transient %s on %s (attempt %d/%d). Retrying in %.1fs...",
                                typed_err.category,
                                model_name,
                                attempt + 1,
                                max_retries_per_model,
                                sleep_sec,
                            )
                            time.sleep(sleep_sec)
                            delay *= 2
                            continue
                        logger.warning("Max retries exceeded on %s; cascading to next model...", model_name)
                        break

                    logger.error("Unexpected error on %s: %s", model_name, str(exc))
                    break

        final_err_msg = last_error.message if isinstance(last_error, GeminiError) else str(last_error)
        logger.critical("All candidate Gemini models failed. Last error: %s", final_err_msg)
        if isinstance(last_error, GeminiError):
            raise last_error
        raise GeminiError(f"AI generation failed across all models: {final_err_msg}")

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries_per_model: int = 2,
    ) -> str:
        """Generate freeform plain text response with model cascading."""
        client = self.get_client()
        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]

        last_error: Exception | None = None

        for model_name in candidate_models:
            delay = 1.0
            for attempt in range(max_retries_per_model):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=temperature),
                    )
                    if response.text:
                        return response.text.strip()
                    raise GeminiError("Model returned empty text response.")
                except Exception as exc:
                    typed_err = self.categorize_exception(exc)
                    last_error = typed_err
                    if isinstance(typed_err, GeminiAuthError):
                        raise typed_err
                    if attempt < max_retries_per_model - 1:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    break

        if isinstance(last_error, GeminiError):
            raise last_error
        raise GeminiError(f"Text generation failed: {last_error}")

    def embed_texts(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        max_retries: int = 3,
    ) -> list[list[float]]:
        """Generate vector embeddings using configured embedding model with retry backoff."""
        if not texts:
            return []

        client = self.get_client()
        delay = 1.0
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                resp = client.models.embed_content(
                    model=self.embed_model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [e.values for e in resp.embeddings]
            except Exception as exc:
                typed_err = self.categorize_exception(exc)
                last_error = typed_err
                if isinstance(typed_err, GeminiAuthError):
                    raise typed_err
                if attempt < max_retries - 1:
                    sleep_sec = delay + random.uniform(0.2, 0.6)
                    time.sleep(sleep_sec)
                    delay *= 2
                    continue
                raise typed_err

        raise last_error or GeminiError("Embedding failed.")

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        max_retries: int = 2,
    ) -> str:
        """
        Transcribe an audio recording using Gemini multimodal audio capabilities.
        """
        client = self.get_client()
        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]

        prompt = (
            "You are an expert audio transcription system. "
            "Accurately transcribe the spoken answer from this audio recording verbatim. "
            "Output ONLY the plain transcription text. Do not include commentary, notes, timestamps, or headers. "
            "If the audio is completely silent or inaudible, return '[Inaudible]'."
        )

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)

        for model_name in candidate_models:
            delay = 1.0
            for attempt in range(max_retries):
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=[audio_part, prompt],
                    )
                    text = resp.text.strip() if resp.text else ""
                    return text or "[No speech detected]"
                except Exception as exc:
                    typed_err = self.categorize_exception(exc)
                    if isinstance(typed_err, GeminiAuthError):
                        raise typed_err
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    break

        raise GeminiError("Audio transcription failed across available models.")

    def check_health(self, test_call: bool = False) -> dict[str, Any]:
        """
        Diagnostic probe verifying Gemini configuration and optionally running a test inference.
        """
        configured = bool(self._api_key)
        diagnostic: dict[str, Any] = {
            "configured": configured,
            "primary_model": self.primary_model,
            "fallback_models": self.fallback_models,
            "embed_model": self.embed_model,
            "key_present": configured,
            "key_masked": f"{self._api_key[:6]}...{self._api_key[-4:]}" if (configured and len(self._api_key) > 10) else None,
            "status": "ready" if configured else "missing_key",
        }

        if not configured:
            diagnostic["message"] = "GEMINI_API_KEY is not configured in backend environment."
            return diagnostic

        if test_call:
            t0 = time.time()
            try:
                client = self.get_client()
                resp = client.models.generate_content(
                    model=self.primary_model,
                    contents="Reply with 'OK'",
                )
                diagnostic["test_call"] = {
                    "status": "success",
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "response": resp.text.strip() if resp.text else "OK",
                    "active_model": self.primary_model,
                }
                diagnostic["status"] = "healthy"
            except Exception as exc:
                cat_err = self.categorize_exception(exc)
                diagnostic["test_call"] = {
                    "status": "error",
                    "category": cat_err.category,
                    "error": cat_err.message,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                }
                diagnostic["status"] = "degraded"

        return diagnostic


# Global singleton instance for application use
gemini_service = GeminiService()
