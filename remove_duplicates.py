import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mileage_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count

# Find emails with duplicates
duplicate_emails = User.objects.values('email').annotate(
    email_count=Count('email')
).filter(email_count__gt=1)

if not duplicate_emails:
    print("✅ No duplicate emails found!")
else:
    print(f"Found {len(duplicate_emails)} email(s) with duplicates:\n")
    
    for dup in duplicate_emails:
        email = dup['email']
        users = User.objects.filter(email=email).order_by('date_joined')
        
        print(f"\n📧 Email: {email}")
        print(f"   Total users: {users.count()}")
        
        # Keep the most recent user, delete others
        users_to_delete = list(users)[:-1]  # All except the last one
        keep_user = users.last()
        
        print(f"   ✓ Keeping: {keep_user.username} (ID: {keep_user.id}, joined: {keep_user.date_joined})")
        
        for user in users_to_delete:
            print(f"   ✗ Deleting: {user.username} (ID: {user.id}, joined: {user.date_joined})")
            user.delete()
    
    print("\n✅ Duplicate removal complete!")
