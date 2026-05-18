from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        COACH = "COACH", "Coach"
        MEMBER = "MEMBER", "Member"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    school = models.CharField(max_length=128, blank=True)
    real_name = models.CharField(max_length=64, blank=True)

    @property
    def is_coach_or_admin(self):
        return self.role in {self.Role.ADMIN, self.Role.COACH} or self.is_staff
