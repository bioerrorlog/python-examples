"""Call the deployed POST endpoints through IAP and write each response to a file.

This is the first stage of the two-stage e2e flow: this script performs the
network calls, and tests/e2e/test_api.py verifies the recorded results without
touching the network. Run it directly, not through pytest:

    uv run tests/e2e/exe_api_calls/main.py

Request bodies live in data/, one directory per endpoint and one JSON file per
case, e.g. data/echo/hello.json is POSTed to /echo. Its response is written to
results/<run>/echo/hello/result.json, where <run> is the UTC start time of the
run, so earlier runs are kept side by side. Adding a case means adding a file
under data/, with no change to this script.

IAP on Cloud Run uses a Google-managed OAuth client, so the usual OIDC ID token
flow is unavailable. IAP does accept a service account self-signed JWT whose
audience is the service URL. The JWT is signed through the IAM Credentials API
with the local user's credentials, so no service account key is needed.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import google.auth
import requests
from google.auth.transport.requests import AuthorizedSession


SERVICE_URL = "https://fastapi-gcp-xxxxxxxxxx.asia-northeast1.run.app"
SERVICE_ACCOUNT = "fastapi-gcp-client@your-gcp-project-id.iam.gserviceaccount.com"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"


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


def call(path: str, body: dict, token: str) -> dict:
    """POST one request body and record the response.

    IAP verifies the bearer token first and forwards the request to Cloud Run
    only when the service account is allowed to access the resource, so every
    response recorded here comes from the service itself.
    """
    response = requests.post(
        f"{SERVICE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
        timeout=30,
    )
    return {
        "path": path,
        "body": body,
        "status_code": response.status_code,
        "json": response.json(),
    }


def main() -> None:
    """POST every test data file to its endpoint and write one result file per case.

    Input: data/<endpoint>/<case>.json, each holding a request body. The parent
    directory name is the endpoint, so data/echo/hello.json is POSTed to /echo.

    Output: results/<run>/<endpoint>/<case>/result.json, where <run> is the UTC
    start time of this run. Each file holds the request and the response on its
    own, so a run is a directory tree mirroring data/. tests/e2e/test_api.py
    reads the most recent run and verifies it.
    """
    token = sign_jwt()

    testdata_paths = sorted(DATA_DIR.glob("*/*.json"))
    if not testdata_paths:
        raise SystemExit(f"no test data found in {DATA_DIR}")

    started_at = datetime.now(timezone.utc)
    run_dir = RESULTS_DIR / started_at.strftime("%Y%m%dT%H%M%SZ")
    for testdata_path in testdata_paths:
        endpoint = testdata_path.parent.name
        case = testdata_path.stem
        result = {
            "service_url": SERVICE_URL,
            "collected_at": started_at.isoformat(),
            **call(f"/{endpoint}", json.loads(testdata_path.read_text()), token),
        }

        result_path = run_dir / endpoint / case / "result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"{endpoint}/{case}: POST /{endpoint} -> {result['status_code']}")

    print(f"wrote {len(testdata_paths)} results under {run_dir}")


if __name__ == "__main__":
    main()
