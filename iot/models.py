from django.db import models

class IoTDevice(models.Model):
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=50, unique=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    firmware_version = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.device_id})"
