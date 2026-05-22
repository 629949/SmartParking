from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from parking.models import ParkingSlot, IoTCommand

@staff_member_required
def iot_control(request):
    slots = ParkingSlot.objects.all()
    commands = IoTCommand.objects.all()[:20]
    return render(request, 'iot/control_panel.html', {'slots': slots, 'commands': commands})
