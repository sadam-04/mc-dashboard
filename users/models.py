from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    mc_username = models.CharField(max_length=16, unique=True)
    mc_uuid = models.CharField(max_length=36, unique=True, blank=True)

    def __str__(self):
        return f"{self.user.username} (MC: {self.mc_username}/{self.mc_uuid})"
# class MyUser(AbstractUser):
#     name = models.CharField(max_length=16)

#     def __str__(self):
#         return self.username