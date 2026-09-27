from cryptography.fernet import Fernet, InvalidToken


class TokenCipherError(ValueError):
    pass


class TokenCipher:
    def __init__(self, encryption_key: str) -> None:
        try:
            self._fernet = Fernet(encryption_key.encode())
        except (ValueError, TypeError) as exc:
            raise TokenCipherError("Invalid LinkedIn token encryption key") from exc

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise TokenCipherError("Unable to decrypt LinkedIn token") from exc

