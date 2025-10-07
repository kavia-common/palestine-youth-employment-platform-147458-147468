from typing import Optional


# PUBLIC_INTERFACE
def send_sms(phone: str, message: str, api_key: Optional[str] = None) -> bool:
    """Stub SMS sender. Integrate with real provider later."""
    # TODO: Implement provider integration using SMS_PROVIDER_API_KEY
    return True
