from django.db import models

import uuid
from AuthN.models import AdminProfile 
from django.core.exceptions import ValidationError

class ServiceShift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_time = models.DateTimeField()
    to_time = models.DateTimeField()
    admin = models.ForeignKey(AdminProfile, on_delete=models.CASCADE, related_name='service_shifts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shift_name = models.CharField(max_length=100)
    is_inactive = models.BooleanField(default=False)
    shift_duration = models.DurationField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.from_time and self.to_time:
            self.shift_duration = self.to_time - self.from_time
        super(ServiceShift, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.shift_name} ({self.from_time} - {self.to_time})"
