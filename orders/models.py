from django.db import models
import uuid

# Create your models here.

class PaymentToken(models.Model):
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    country = models.CharField(max_length=2, null=True, blank=True)
    user_count = models.IntegerField(default=1)
    password = models.CharField(max_length=255)  # Store the generated password
    
    def __str__(self):
        return f"{self.email} - {self.token}"
