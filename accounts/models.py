from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


class User(AbstractUser):
    """Custom user model. This user class is what we will be using"""

    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    username = models.CharField(max_length=255, blank=True, default="")
    # last_activity = models.DateTimeField(default=now)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)
    # bio = models.TextField(blank=True, default="")
    # profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    # phone = models.CharField(max_length=255, blank=True, default="")
    # address = models.CharField(max_length=255, blank=True, default="")
    # city = models.CharField(max_length=255, blank=True, default="")
    # state = models.CharField(max_length=255, blank=True, default="")
    # country = models.CharField(max_length=255, blank=True, default="")
    # zip_code = models.CharField(max_length=255, blank=True, default="")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return f"User: {self.pk} - {self.email}"

    def save(self, *args, **kwargs) -> None:
        self.updated_at = now()
        return super().save(*args, **kwargs)


class BLToken(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Blacklisted Token: {self.pk} for {self.user.email}"
