from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import PorterPartner, UserProfile


class Command(BaseCommand):
    help = 'Create 5 porter service providers with realistic data'

    def handle(self, *args, **options):
        porters_data = [
            {
                'name': 'SwiftDeliver Express',
                'email': 'contact@swiftdeliver.com',
                'phone': '+91-9876543210',
                'tracking_url': 'https://swiftdeliver.com/track?id=',
            },
            {
                'name': 'MediCourier Services',
                'email': 'support@medicourier.com',
                'phone': '+91-9123456789',
                'tracking_url': 'https://medicourier.com/tracking?ref=',
            },
            {
                'name': 'HealthExpress Logistics',
                'email': 'hello@healthexpress.in',
                'phone': '+91-8765432109',
                'tracking_url': 'https://healthexpress.in/track/',
            },
            {
                'name': 'QuickShip Delivery',
                'email': 'ops@quickship.com',
                'phone': '+91-7654321098',
                'tracking_url': 'https://quickship.com/shipment/',
            },
            {
                'name': 'CarePlus Logistics',
                'email': 'dispatch@careplus.com',
                'phone': '+91-6543210987',
                'tracking_url': 'https://careplus.com/track?code=',
            },
        ]

        created_count = 0
        for porter_data in porters_data:
            porter, created = PorterPartner.objects.get_or_create(
                name=porter_data['name'],
                defaults={
                    'contact_email': porter_data['email'],
                    'contact_phone': porter_data['phone'],
                    'external_tracking_url': porter_data['tracking_url'],
                    'active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {porter.name}')
                )
                self.stdout.write(f'  Email: {porter.contact_email}')
                self.stdout.write(f'  Phone: {porter.contact_phone}')
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Already exists: {porter.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total porter services created: {created_count}')
        )
        
        # Also create porter admin user accounts for testing
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Creating Porter Admin User Accounts...')
        self.stdout.write('='*60)
        
        porter_users = [
            {'username': 'porter_swift', 'email': 'admin@swiftdeliver.com', 'name': 'Swift Deliver Admin'},
            {'username': 'porter_medi', 'email': 'admin@medicourier.com', 'name': 'MediCourier Admin'},
            {'username': 'porter_health', 'email': 'admin@healthexpress.in', 'name': 'HealthExpress Admin'},
            {'username': 'porter_quick', 'email': 'ops@quickship.com', 'name': 'QuickShip Admin'},
            {'username': 'porter_care', 'email': 'dispatch@careplus.com', 'name': 'CarePlus Admin'},
        ]
        
        user_created_count = 0
        for user_data in porter_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['name'].split()[0],
                    'last_name': ' '.join(user_data['name'].split()[1:]),
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password('adarsh123')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'admin', 'is_verified': True}
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created user: {user.username}')
                )
                self.stdout.write(f'  Password: adarsh123')
                user_created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ User already exists: {user.username}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total porter admin users created: {user_created_count}')
        )
