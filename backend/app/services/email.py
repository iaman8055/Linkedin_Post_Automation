from typing import Protocol


class AuthenticationEmailSender(Protocol):
    """Port implemented by a real transactional email provider in a later integration phase."""

    def send_verification(self, recipient: str, token: str) -> None: ...

    def send_password_reset(self, recipient: str, token: str) -> None: ...

