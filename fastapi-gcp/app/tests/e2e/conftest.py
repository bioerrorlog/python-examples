"""Authentication helpers for calling the deployed, IAP-protected service.

IAP on Cloud Run uses a Google-managed OAuth client, so the usual OIDC ID token
flow is unavailable. IAP does accept a service account self-signed JWT whose
audience is the service URL. The JWT is signed through the IAM Credentials API
with the local user's credentials, so no service account key is needed.
"""

import json
import time

import google.auth
import pytest
import requests
from google.auth.transport.requests import AuthorizedSession


SERVICE_URL = "https://fastapi-gcp-xxxxxxxxxx.asia-northeast1.run.app"
SERVICE_ACCOUNT = "fastapi-gcp-client@your-gcp-project-id.iam.gserviceaccount.com"


@pytest.fixture(scope="session")
def signed_jwt() -> str:
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


@pytest.fixture(scope="session")
def call(signed_jwt: str):
    """Return a function that sends an authenticated request through IAP.

    IAP verifies the bearer token first and forwards the request to Cloud Run
    only when the service account is allowed to access the resource.
    """

    def _call(method: str, path: str, body: dict | None = None) -> requests.Response:
        return requests.request(
            method,
            f"{SERVICE_URL}{path}",
            headers={"Authorization": f"Bearer {signed_jwt}"},
            json=body,
            timeout=30,
        )

    return _call
