import asyncio

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fastapi-gcp")

SLOW_HELLO_DELAY_SECONDS = 5


class EchoRequest(BaseModel):
    text: str


class SlowHelloRequest(BaseModel):
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


@app.post("/slow-hello")
async def slow_hello(request: SlowHelloRequest):
    await asyncio.sleep(SLOW_HELLO_DELAY_SECONDS)
    return {"message": f"Hello, {request.text}"}
