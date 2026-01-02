from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create groups in database for each designation'

    def handle(self, *args, **kwargs):
        designations = [
            'PM',
            'PRC',
            'TS',
            'GE',
            'M&E',
            'PUM',
            'WT',
            'IT',
            'Finance',
            'Admin',
        ]
        
        created_count = 0
        existing_count = 0
        
        for designation in designations:
            group, created = Group.objects.get_or_create(name=designation)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created group: {designation}'))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f'- Group already exists: {designation}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'  Existing: {existing_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {len(designations)}'))
