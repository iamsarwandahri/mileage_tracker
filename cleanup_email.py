import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mileage_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import PendingUserRegistration

# Enter the email you want to delete
email_to_delete = input("Enter the email address to delete: ")

# Delete from User table
user_deleted = User.objects.filter(email=email_to_delete).delete()
print(f"Deleted from User table: {user_deleted}")

# Delete from PendingUserRegistration table
pending_deleted = PendingUserRegistration.objects.filter(email=email_to_delete).delete()
print(f"Deleted from PendingUserRegistration table: {pending_deleted}")

print(f"\n✅ Email '{email_to_delete}' has been removed from both tables!")
print("You can now register with this email again.")
