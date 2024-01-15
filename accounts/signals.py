from django.dispatch import Signal

verification_token_created = Signal(["instance", "verification_token"])

pwd_reset_token_created = Signal(["instance", "password_reset"])
