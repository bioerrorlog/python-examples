"""Call the IAP-protected Cloud Run service with a service account self-signed JWT.

IAP on Cloud Run uses a Google-managed OAuth client, so the usual OIDC ID token
flow is unavailable. IAP does accept a service account self-signed JWT whose
audience is the service URL. The JWT is signed through the IAM Credentials API
with the local user's credentials, so no service account key is needed.
"""

import json
import os
import time

import google.auth
import requests
from google.auth.transport.requests import AuthorizedSession

SERVICE_URL = os.environ["SERVICE_URL"]
SERVICE_ACCOUNT = os.environ["SERVICE_ACCOUNT"]


def sign_jwt() -> str:
    """Return a JWT signed as the client service account, valid for one hour.

    The local user's credentials (ADC) are used to call the IAM Credentials API,
    which signs the payload on behalf of the service account. This requires
    roles/iam.serviceAccountTokenCreator on that service account. IAP checks the
    iss/sub claims against roles/iap.httpsResourceAccessor, and the aud claim
    against the URL of the protected resource.
    """
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    now = int(time.time())
    payload = {
        "iss": SERVICE_ACCOUNT,
        "sub": SERVICE_ACCOUNT,
        "aud": SERVICE_URL,
        "iat": now,
        "exp": now + 3600,
    }
    response = AuthorizedSession(credentials).post(
        f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{SERVICE_ACCOUNT}:signJwt",
        json={"payload": json.dumps(payload)},
    )
    response.raise_for_status()
    return response.json()["signedJwt"]


def call(method: str, path: str, body: dict | None = None) -> requests.Response:
    """Send a request to the service, authenticating to IAP with a fresh JWT.

    IAP verifies the bearer token first and forwards the request to Cloud Run
    only when the service account is allowed to access the resource.
    """
    return requests.request(
        method,
        f"{SERVICE_URL}{path}",
        headers={"Authorization": f"Bearer {sign_jwt()}"},
        json=body,
        timeout=30,
    )


if __name__ == "__main__":
    root = call("GET", "/")
    print(f"GET / -> {root.status_code} {root.text}")

    health = call("GET", "/health")
    print(f"GET /health -> {health.status_code} {health.text}")

    echo = call("POST", "/echo", {"text": "hello"})
    print(f"POST /echo -> {echo.status_code} {echo.text}")
