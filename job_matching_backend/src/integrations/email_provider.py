from typing import Optional


# PUBLIC_INTERFACE
def send_email(to: str, subject: str, body: str, api_key: Optional[str] = None) -> bool:
    """Stub email sender. Integrate with real provider later."""
    # TODO: Implement provider integration using EMAIL_PROVIDER_API_KEY
    return True
