"""Call the deployed POST endpoints through IAP and write each response to a file.

This is the first stage of the two-stage e2e flow: this script performs the
network calls, and tests/e2e/test_api.py verifies the recorded results without
touching the network. Run it directly, not through pytest:

    uv run tests/e2e/exe_api_calls/main.py

Request bodies live in data/, one directory per endpoint and one JSON file per
case, e.g. data/echo/hello.json is POSTed to /echo. Each case gets its own
directory under results/<run>/<endpoint>/<case>/, holding request.json (the body
sent), response.json (the body received) and meta.json (everything else about
the response). <run> is the UTC start time of the run, so earlier runs are kept
side by side. Adding a case means adding a file under data/, with no change to
this script.

Some endpoints are slow, so all cases are called concurrently and the run takes
about as long as its slowest case. Each result is written as its response
arrives, so the printed order is completion order, not data/ order.

IAP on Cloud Run uses a Google-managed OAuth client, so the usual OIDC ID token
flow is unavailable. IAP does accept a service account self-signed JWT whose
audience is the service URL. The JWT is signed through the IAM Credentials API
with the local user's credentials, so no service account key is needed.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import google.auth
import httpx
from google.auth.transport.requests import AuthorizedSession


SERVICE_URL = "https://fastapi-gcp-xxxxxxxxxx.asia-northeast1.run.app"
SERVICE_ACCOUNT = "fastapi-gcp-client@your-gcp-project-id.iam.gserviceaccount.com"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
TIMEOUT_SECONDS = 30


def sign_jwt() -> str:
    """Return a JWT signed as the client service account, valid for one hour.

    The local user's credentials (ADC) are used to call the IAM Credentials API,
    which signs the payload on behalf of the service account. This requires
    roles/iam.serviceAccountTokenCreator on that service account. IAP checks the
    iss/sub claims against roles/iap.httpsResourceAccessor, and the aud claim
    against the requested URL.
    """
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    now = int(time.time())
    payload = {
        "iss": SERVICE_ACCOUNT,
        "sub": SERVICE_ACCOUNT,
        "aud": f"{SERVICE_URL}/*",
        "iat": now,
        "exp": now + 3600,
    }
    response = AuthorizedSession(credentials).post(
        f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{SERVICE_ACCOUNT}:signJwt",
        json={"payload": json.dumps(payload)},
    )
    response.raise_for_status()
    return response.json()["signedJwt"]


async def call(
    client: httpx.AsyncClient, path: str, body: dict, token: str
) -> tuple[dict, dict]:
    """POST one request body and return the response body and its metadata.

    IAP verifies the bearer token first and forwards the request to Cloud Run
    only when the service account is allowed to access the resource, so every
    response recorded here comes from the service itself.
    """
    response = await client.post(
        f"{SERVICE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    meta = {
        "method": "POST",
        "path": path,
        "status_code": response.status_code,
        "elapsed_seconds": response.elapsed.total_seconds(),
        "response_headers": dict(response.headers),
    }
    return response.json(), meta


def write_json(path: Path, data: dict) -> None:
    """Write one JSON file, creating its directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


async def run_case(
    client: httpx.AsyncClient,
    testdata_path: Path,
    token: str,
    run_dir: Path,
    started_at: datetime,
) -> None:
    """POST one test data file and write the three result files for that case.

    Two lines are printed per case, one when the request goes out and one when
    the response comes back, so a slow case is visible while it is still in
    flight. The lines of different cases interleave.
    """
    endpoint = testdata_path.parent.name
    case = testdata_path.stem
    request_body = json.loads(testdata_path.read_text())
    print(f"--> {endpoint}/{case}: POST /{endpoint}", flush=True)
    response_body, meta = await call(client, f"/{endpoint}", request_body, token)

    case_dir = run_dir / endpoint / case
    write_json(case_dir / "request.json", request_body)
    write_json(case_dir / "response.json", response_body)
    write_json(
        case_dir / "meta.json",
        {
            "service_url": SERVICE_URL,
            "collected_at": started_at.isoformat(),
            **meta,
        },
    )
    print(
        f"<-- {endpoint}/{case}: {meta['status_code']}"
        f" in {meta['elapsed_seconds']:.1f}s",
        flush=True,
    )


async def main() -> None:
    """POST every test data file to its endpoint and write three files per case.

    Input: data/<endpoint>/<case>.json, each holding a request body. The parent
    directory name is the endpoint, so data/echo/hello.json is POSTed to /echo.

    Output: results/<run>/<endpoint>/<case>/, where <run> is the UTC start time
    of this run, holding request.json (the body sent, a copy of the test data),
    response.json (the body received) and meta.json (the service URL, the
    timestamp, and the response information other than the body).
    tests/e2e/test_api.py reads the most recent run and verifies it.

    All cases are in flight at once. One failing case does not cancel the
    others: the exceptions are collected and reported once every call is done.
    """
    token = sign_jwt()

    testdata_paths = sorted(DATA_DIR.glob("*/*.json"))
    if not testdata_paths:
        raise SystemExit(f"no test data found in {DATA_DIR}")

    started_at = datetime.now(timezone.utc)
    run_dir = RESULTS_DIR / started_at.strftime("%Y%m%dT%H%M%SZ")
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        results = await asyncio.gather(
            *(
                run_case(client, testdata_path, token, run_dir, started_at)
                for testdata_path in testdata_paths
            ),
            return_exceptions=True,
        )

    failures = [
        (path, result)
        for path, result in zip(testdata_paths, results)
        if isinstance(result, BaseException)
    ]
    for path, error in failures:
        print(f"<-- {path.parent.name}/{path.stem}: failed: {error!r}")

    written = len(testdata_paths) - len(failures)
    print(f"wrote {written} results under {run_dir}")
    if failures:
        raise SystemExit(f"{len(failures)} of {len(testdata_paths)} cases failed")


if __name__ == "__main__":
    asyncio.run(main())
