from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fastapi-gcp")


class EchoRequest(BaseModel):
    text: str


@app.get("/")
def root():
    return {"message": "Hello, FastAPI on GCP"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/echo")
def echo(request: EchoRequest):
    return {"text": request.text}
