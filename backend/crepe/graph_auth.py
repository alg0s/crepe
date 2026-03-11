from __future__ import annotations

from msal import ConfidentialClientApplication

from crepe.config import Config


class GraphAuthenticator:
    """Acquire Microsoft Graph tokens using confidential client auth."""

    def __init__(self, config: Config) -> None:
        authority = f"https://login.microsoftonline.com/{config.tenant_id}"
        self._app = ConfidentialClientApplication(
            client_id=config.client_id,
            authority=authority,
            client_credential=config.client_secret,
        )

    def get_access_token(self) -> str:
        result = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        token = result.get("access_token")
        if not token:
            details = result.get("error_description") or result.get("error") or "unknown auth error"
            raise RuntimeError(f"Failed to acquire Microsoft Graph token: {details}")
        return token

