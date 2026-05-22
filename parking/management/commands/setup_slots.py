from django.core.management.base import BaseCommand
from parking.models import ParkingSlot

class Command(BaseCommand):
    help = 'Create the 9 parking slots'

    def handle(self, *args, **kwargs):
        ParkingSlot.objects.all().delete()
        cols = {1: 'A', 2: 'B', 3: 'C'}
        for level in [1, 2, 3]:
            for col in [1, 2, 3]:
                ParkingSlot.objects.create(
                    level=level, column=col,
                    slot_number=f"L{level}{cols[col]}",
                    status='available'
                )
        self.stdout.write(self.style.SUCCESS('Created 9 parking slots.'))
