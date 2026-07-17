from fastapi import FastAPI

from app.schemas import SpeechPrepareRequest, SpeechPrepareResponse

app = FastAPI(title="OpenSign Darija Speech Mock")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "mode": "mock"}


@app.post("/prepare", response_model=SpeechPrepareResponse)
def prepare(payload: SpeechPrepareRequest) -> SpeechPrepareResponse:
    return SpeechPrepareResponse(
        status="not_implemented",
        message="La synthese vocale sera integree dans une phase ulterieure.",
        contract=payload.model_dump(),
    )
