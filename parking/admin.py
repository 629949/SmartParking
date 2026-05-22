from django.contrib import admin
from .models import ParkingSlot, ParkingSession, Payment, Receipt, IoTCommand

@admin.register(ParkingSlot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['slot_number', 'level', 'column', 'status', 'last_updated']
    list_filter = ['level', 'status']
    list_editable = ['status']

@admin.register(ParkingSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'slot', 'vehicle_plate', 'check_in', 'check_out', 'status']
    list_filter = ['status']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'session', 'amount_ugx', 'method', 'status', 'paid_at']
    list_filter = ['status', 'method']

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'payment', 'issued_at']

@admin.register(IoTCommand)
class IoTCommandAdmin(admin.ModelAdmin):
    list_display = ['id', 'command', 'target_level', 'target_column', 'status', 'created_at']
    list_filter = ['command', 'status']
