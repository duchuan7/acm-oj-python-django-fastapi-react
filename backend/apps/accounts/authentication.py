from django.utils import timezone
from rest_framework.authentication import TokenAuthentication


class LastSeenTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        user.last_seen_at = timezone.now()
        user.save(update_fields=["last_seen_at"])
        return user, token
