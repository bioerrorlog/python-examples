from fastapi import FastAPI

app = FastAPI(title="fastapi-gcp")


@app.get("/")
def root():
    return {"message": "Hello, FastAPI on GCP"}


@app.get("/health")
def health():
    return {"status": "ok"}
