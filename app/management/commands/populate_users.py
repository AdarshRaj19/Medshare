from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import UserProfile
import random

class Command(BaseCommand):
    help = 'Create 10 real users for each role (ngo, donor, individual) with password adarsh123.'

    def handle(self, *args, **options):
        roles = ['ngo', 'donor', 'individual']
        created = 0
        for role in roles:
            for i in range(1, 11):
                username = f'{role}{i}'
                email = f'{role}{i}@example.com'
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='adarsh123',
                        first_name=role.capitalize(),
                        last_name=str(i)
                    )
                    UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'role': role,
                            'organization_name': f'{role.capitalize()} Org {i}' if role == 'ngo' else '',
                            'phone': f'99999{random.randint(10000,99999)}'
                        }
                    )
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created} users (10 per role).'))
