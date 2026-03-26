from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class NATAPrepException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class QuestionBankEmptyError(NATAPrepException):
    def __init__(self, concept_name: str = ""):
        super().__init__(
            f"No questions available{' for ' + concept_name if concept_name else ''}. "
            "Run the question generation agent to populate the bank.",
            status_code=404,
        )


class EvaluationTimeoutError(NATAPrepException):
    def __init__(self):
        super().__init__("Drawing evaluation timed out. Please try again.", status_code=503)


async def nataprepexception_handler(request: Request, exc: NATAPrepException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
