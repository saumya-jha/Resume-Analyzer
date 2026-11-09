"""Single place that talks to the Groq API.

* The client is created on first use, so the server starts (and /health
  works) even when the API key is missing; AI endpoints then answer with a
  clear 503 instead of crashing at import time.
* Every Groq failure is translated into one of our own errors (rate limit,
  unavailable, bad response) with a safe message; details go to the log only.
* If the model returns JSON that does not fit the expected schema, the call
  is retried once before giving up.
"""

import logging
import re
from functools import lru_cache

import groq
from groq import Groq
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import (
    LLMConfigError,
    LLMError,
    LLMRateLimitError,
    LLMUnavailableError,
)

logger = logging.getLogger(__name__)

# Kept as a module constant for older code / scripts
MODEL = settings.groq_model


@lru_cache(maxsize=1)
def get_client() -> Groq:

    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY is not set. Add it to backend/.env")
        raise LLMConfigError()

    return Groq(
        api_key=settings.groq_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def __getattr__(name: str):
    # Backwards compatibility: `from app.services.groq_client import client`
    if name == "client":
        return get_client()

    raise AttributeError(name)


def prepare_untrusted_text(text: str, tag: str) -> str:
    """Wrap user-supplied text in tags and strip anything that could close them.

    Resumes and job descriptions are DATA, not instructions. The prompts tell
    the model to ignore any commands found between these tags, and removing
    look-alike tags stops the text from "escaping" its block.
    """

    text = (text or "")[: settings.max_resume_chars]

    text = re.sub(rf"</?\s*{tag}\s*>", " ", text, flags=re.IGNORECASE)

    return f"<{tag}>\n{text}\n</{tag}>"


def generate_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[BaseModel],
    attempts: int = 2,
):
    """Ask the model for JSON and return it validated as `schema`."""

    last_error = None

    for attempt in range(1, attempts + 1):

        try:
            response = get_client().chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )

        except LLMError:
            raise

        except groq.RateLimitError as error:
            logger.warning("Groq rate limit reached: %s", error)
            raise LLMRateLimitError() from error

        except (groq.AuthenticationError, groq.PermissionDeniedError) as error:
            logger.error("Groq rejected the API key: %s", error)
            raise LLMConfigError() from error

        except (groq.APITimeoutError, groq.APIConnectionError) as error:
            logger.warning("Could not reach Groq: %s", error)
            raise LLMUnavailableError() from error

        except groq.APIStatusError as error:
            logger.error("Groq API error %s: %s", error.status_code, error)

            if error.status_code >= 500:
                raise LLMUnavailableError() from error

            raise LLMError() from error

        try:
            content = response.choices[0].message.content or ""

            return schema.model_validate_json(content)

        except (ValueError, IndexError, AttributeError) as error:
            # pydantic's ValidationError is a ValueError
            last_error = error
            logger.warning(
                "Model returned invalid JSON (attempt %s of %s): %s",
                attempt, attempts, error,
            )

    raise LLMError() from last_error
