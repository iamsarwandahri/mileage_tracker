from django.core.management.base import BaseCommand
from mileage.models import MileageRecord

class Command(BaseCommand):
    help = 'Recalculate distance and status for all mileage records'

    def handle(self, *args, **options):
        records = MileageRecord.objects.all()
        updated_count = 0
        
        for record in records:
            if record.start_km and record.end_km:
                old_distance = record.distance
                old_status = record.status
                
                # Force recalculation
                record.save()
                
                if record.distance != old_distance or record.status != old_status:
                    updated_count += 1
                    self.stdout.write(
                        f'Updated record {record.id}: distance {old_distance} -> {record.distance}, status {old_status} -> {record.status}'
                    )
        
        self.stdout.write(f'Successfully updated {updated_count} records')