from django.db import models
import uuid

# Create your models here.

class PaymentToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    country = models.CharField(max_length=2, default='US')  # ISO country code
    user_count = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.email} - {self.token}"
