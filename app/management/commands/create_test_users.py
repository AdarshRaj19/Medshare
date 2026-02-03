from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import UserProfile


class Command(BaseCommand):
    help = 'Create 5 users each for NGO, Donor, and Individual roles with realistic data'

    def handle(self, *args, **options):
        password = 'adarsh123'
        
        # Donor data
        donors_data = [
            {
                'username': 'donor_rajesh',
                'email': 'rajesh.sharma@gmail.com',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'organization_name': 'Sharma Medical Solutions',
                'latitude': 28.6139,
                'longitude': 77.2090,
            },
            {
                'username': 'donor_priya',
                'email': 'priya.doctor@yahoo.com',
                'first_name': 'Priya',
                'last_name': 'Kapoor',
                'organization_name': 'Kapoor Clinic',
                'latitude': 19.0760,
                'longitude': 72.8777,
            },
            {
                'username': 'donor_vikram',
                'email': 'vikram.pharmacy@outlook.com',
                'first_name': 'Vikram',
                'last_name': 'Singh',
                'organization_name': 'Vikram Pharmacy',
                'latitude': 23.1815,
                'longitude': 79.9864,
            },
            {
                'username': 'donor_neha',
                'email': 'neha.medical@gmail.com',
                'first_name': 'Neha',
                'last_name': 'Gupta',
                'organization_name': 'Gupta Medical Store',
                'latitude': 12.9716,
                'longitude': 77.5946,
            },
            {
                'username': 'donor_arjun',
                'email': 'arjun.healthcare@hotmail.com',
                'first_name': 'Arjun',
                'last_name': 'Patel',
                'organization_name': 'Patel Healthcare',
                'latitude': 21.1458,
                'longitude': 79.0882,
            },
        ]
        
        # NGO data
        ngos_data = [
            {
                'username': 'ngo_care_mumbai',
                'email': 'mumbai@careforall.org',
                'first_name': 'Care',
                'last_name': 'For All',
                'organization_name': 'Care For All - Mumbai',
                'latitude': 19.0760,
                'longitude': 72.8777,
            },
            {
                'username': 'ngo_health_delhi',
                'email': 'delhi@healthaid.in',
                'first_name': 'Health',
                'last_name': 'Aid',
                'organization_name': 'Health Aid Initiative - Delhi',
                'latitude': 28.6139,
                'longitude': 77.2090,
            },
            {
                'username': 'ngo_smile_bengaluru',
                'email': 'bengaluru@smile.co.in',
                'first_name': 'Smile',
                'last_name': 'Foundation',
                'organization_name': 'Smile Foundation - Bengaluru',
                'latitude': 12.9716,
                'longitude': 77.5946,
            },
            {
                'username': 'ngo_life_kolkata',
                'email': 'kolkata@life.org.in',
                'first_name': 'Life',
                'last_name': 'Welfare',
                'organization_name': 'Life Welfare Society - Kolkata',
                'latitude': 22.5726,
                'longitude': 88.3639,
            },
            {
                'username': 'ngo_hope_hyderabad',
                'email': 'hyderabad@hopecares.com',
                'first_name': 'Hope',
                'last_name': 'Cares',
                'organization_name': 'Hope Cares Trust - Hyderabad',
                'latitude': 17.3850,
                'longitude': 78.4867,
            },
        ]
        
        # Individual data
        individuals_data = [
            {
                'username': 'individual_amit',
                'email': 'amit.volunteer@gmail.com',
                'first_name': 'Amit',
                'last_name': 'Kumar',
                'organization_name': 'Independent Volunteer',
                'latitude': 28.6139,
                'longitude': 77.2090,
            },
            {
                'username': 'individual_sarah',
                'email': 'sarah.community@hotmail.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'organization_name': 'Community Helper',
                'latitude': 19.0760,
                'longitude': 72.8777,
            },
            {
                'username': 'individual_rohan',
                'email': 'rohan.help@yahoo.com',
                'first_name': 'Rohan',
                'last_name': 'Nair',
                'organization_name': 'Social Worker',
                'latitude': 12.9716,
                'longitude': 77.5946,
            },
            {
                'username': 'individual_maya',
                'email': 'maya.support@gmail.com',
                'first_name': 'Maya',
                'last_name': 'Desai',
                'organization_name': 'Healthcare Advocate',
                'latitude': 23.1815,
                'longitude': 79.9864,
            },
            {
                'username': 'individual_karan',
                'email': 'karan.medic@outlook.com',
                'first_name': 'Karan',
                'last_name': 'Reddy',
                'organization_name': 'Health Enthusiast',
                'latitude': 17.3850,
                'longitude': 78.4867,
            },
        ]
        
        # Create donors
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Creating DONOR Accounts'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        for donor_data in donors_data:
            user, created = User.objects.get_or_create(
                username=donor_data['username'],
                defaults={
                    'email': donor_data['email'],
                    'first_name': donor_data['first_name'],
                    'last_name': donor_data['last_name'],
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'donor',
                        'organization_name': donor_data['organization_name'],
                        'latitude': donor_data['latitude'],
                        'longitude': donor_data['longitude'],
                        'is_verified': True,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created donor: {user.username}')
                )
                self.stdout.write(f'  Email: {user.email} | Location: ({donor_data["latitude"]}, {donor_data["longitude"]})')
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Donor already exists: {user.username}')
                )
        
        # Create NGOs
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Creating NGO Accounts'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        for ngo_data in ngos_data:
            user, created = User.objects.get_or_create(
                username=ngo_data['username'],
                defaults={
                    'email': ngo_data['email'],
                    'first_name': ngo_data['first_name'],
                    'last_name': ngo_data['last_name'],
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'ngo',
                        'organization_name': ngo_data['organization_name'],
                        'latitude': ngo_data['latitude'],
                        'longitude': ngo_data['longitude'],
                        'is_verified': True,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created NGO: {user.username}')
                )
                self.stdout.write(f'  Email: {user.email} | Organization: {ngo_data["organization_name"]}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ NGO already exists: {user.username}')
                )
        
        # Create Individuals
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Creating INDIVIDUAL Accounts'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        for individual_data in individuals_data:
            user, created = User.objects.get_or_create(
                username=individual_data['username'],
                defaults={
                    'email': individual_data['email'],
                    'first_name': individual_data['first_name'],
                    'last_name': individual_data['last_name'],
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'individual',
                        'organization_name': individual_data['organization_name'],
                        'latitude': individual_data['latitude'],
                        'longitude': individual_data['longitude'],
                        'is_verified': True,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created individual: {user.username}')
                )
                self.stdout.write(f'  Email: {user.email}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'✗ Individual already exists: {user.username}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ All users created successfully!'))
        self.stdout.write(self.style.SUCCESS('Password for all users: adarsh123'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
