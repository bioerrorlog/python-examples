"""Authentication helpers for calling the deployed, IAP-protected service.

IAP on Cloud Run uses a Google-managed OAuth client, so the usual OIDC ID token
flow is unavailable. IAP does accept a service account self-signed JWT whose
audience is the service URL. The JWT is signed through the IAM Credentials API
with the local user's credentials, so no service account key is needed.
"""

import json
import os
import time

import google.auth
import pytest
import requests
from google.auth.transport.requests import AuthorizedSession


@pytest.fixture(scope="session")
def service_url() -> str:
    """URL of the deployed service, from `terraform output -raw service_url`."""
    url = os.environ.get("SERVICE_URL")
    if not url:
        pytest.skip("SERVICE_URL is not set")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def service_account() -> str:
    """Client service account, from `terraform output -raw client_service_account`."""
    email = os.environ.get("SERVICE_ACCOUNT")
    if not email:
        pytest.skip("SERVICE_ACCOUNT is not set")
    return email


@pytest.fixture(scope="session")
def signed_jwt(service_url: str, service_account: str) -> str:
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
        "iss": service_account,
        "sub": service_account,
        "aud": service_url,
        "iat": now,
        "exp": now + 3600,
    }
    response = AuthorizedSession(credentials).post(
        f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{service_account}:signJwt",
        json={"payload": json.dumps(payload)},
    )
    response.raise_for_status()
    return response.json()["signedJwt"]


@pytest.fixture(scope="session")
def call(service_url: str, signed_jwt: str):
    """Return a function that sends an authenticated request through IAP.

    IAP verifies the bearer token first and forwards the request to Cloud Run
    only when the service account is allowed to access the resource.
    """

    def _call(method: str, path: str, body: dict | None = None) -> requests.Response:
        return requests.request(
            method,
            f"{service_url}{path}",
            headers={"Authorization": f"Bearer {signed_jwt}"},
            json=body,
            timeout=30,
        )

    return _call
