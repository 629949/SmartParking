from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class ParkingSlot(models.Model):
    LEVEL_CHOICES = [(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3')]
    COLUMN_CHOICES = [(1, 'Column A'), (2, 'Column B'), (3, 'Column C')]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Maintenance'),
    ]

    level = models.IntegerField(choices=LEVEL_CHOICES)
    column = models.IntegerField(choices=COLUMN_CHOICES)
    slot_number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'column']

    def __str__(self):
        return f"Slot {self.slot_number} (L{self.level}C{self.column}) - {self.status}"

    @property
    def display_name(self):
        cols = {1: 'A', 2: 'B', 3: 'C'}
        return f"L{self.level}-{cols[self.column]}"


class ParkingSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='sessions')
    vehicle_plate = models.CharField(max_length=20)
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-check_in']

    def __str__(self):
        return f"Session {self.session_id} — {self.user.username} @ {self.slot}"

    @property
    def duration_minutes(self):
        end = self.check_out or timezone.now()
        delta = end - self.check_in
        return max(int(delta.total_seconds() / 60), 1)

    @property
    def fee_ugx(self):
        from django.conf import settings
        rate = getattr(settings, 'PARKING_RATE_UGX', 2000)
        hours = max(self.duration_minutes / 60, 0.25)
        return round(hours * rate)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('cash', 'Cash'),
        ('card', 'Card'),
    ]

    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.OneToOneField(ParkingSession, on_delete=models.CASCADE, related_name='payment')
    amount_ugx = models.DecimalField(max_digits=10, decimal_places=0)
    method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='mobile_money')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phone_number = models.CharField(max_length=20, blank=True)
    transaction_ref = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_id} — {self.status} — UGX {self.amount_ugx}"


class Receipt(models.Model):
    receipt_number = models.CharField(max_length=20, unique=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='receipts/', blank=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number}"


class IoTCommand(models.Model):
    COMMAND_CHOICES = [
        ('park', 'Park Vehicle'),
        ('retrieve', 'Retrieve Vehicle'),
        ('home', 'Home Position'),
        ('status', 'Status Check'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('ack', 'Acknowledged'),
        ('done', 'Done'),
        ('error', 'Error'),
    ]

    session = models.ForeignKey(ParkingSession, on_delete=models.CASCADE, related_name='commands', null=True, blank=True)
    command = models.CharField(max_length=20, choices=COMMAND_CHOICES)
    target_level = models.IntegerField(null=True, blank=True)
    target_column = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    payload = models.JSONField(default=dict, blank=True)
    response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.command}] → L{self.target_level}C{self.target_column} ({self.status})"
