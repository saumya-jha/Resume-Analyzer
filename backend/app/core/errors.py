"""Errors the API raises on purpose.

Each error carries the HTTP status code and a message that is safe to show
to the user. Anything unexpected is logged and turned into a generic 500, so
internal details (stack traces, API errors) never reach the client.
"""


class AppError(Exception):

    status_code = 500
    default_detail = "Something went wrong. Please try again."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


# ---- problems with what the user sent ----

class FileValidationError(AppError):
    status_code = 400
    default_detail = "The uploaded file is not valid."


class FileTooLargeError(FileValidationError):
    status_code = 413
    default_detail = "The uploaded file is too large."


class UnprocessableInputError(AppError):
    status_code = 422
    default_detail = "The submitted data could not be processed."


# ---- problems with the AI service ----

class LLMError(AppError):
    status_code = 502
    default_detail = (
        "The AI service returned an unexpected response. Please try again."
    )


class LLMRateLimitError(LLMError):
    status_code = 429
    default_detail = (
        "The AI service is busy right now. Please wait a moment and try again."
    )


class LLMUnavailableError(LLMError):
    status_code = 503
    default_detail = (
        "The AI service is temporarily unavailable. Please try again shortly."
    )


class LLMConfigError(LLMError):
    status_code = 503
    default_detail = "The AI service is not configured correctly on the server."
