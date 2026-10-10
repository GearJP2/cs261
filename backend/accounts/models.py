from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Local application account; this model alone does not verify student status."""
