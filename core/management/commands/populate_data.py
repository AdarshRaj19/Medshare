from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Medicine, UserProfile, DonationRequest, MedicineRating
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample donors
        donors = []
        donor_names = [
            ('John', 'Smith', 'john_smith'),
            ('Sarah', 'Johnson', 'sarah_j'),
            ('Michael', 'Brown', 'mbrown'),
            ('Emma', 'Davis', 'emma_d'),
        ]

        for first, last, username in donor_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': first,
                    'last_name': last,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'donor',
                        'phone': f'555-{random.randint(1000, 9999)}',
                        'latitude': 40.7128 + random.uniform(-0.1, 0.1),
                        'longitude': -74.0060 + random.uniform(-0.1, 0.1),
                    }
                )
            donors.append(user)

        # Create sample NGOs
        ngos = []
        ngo_names = [
            ('Red Cross', 'red_cross'),
            ('City Hospital', 'city_hospital'),
            ('Hope Foundation', 'hope_foundation'),
            ('Medical Relief', 'medical_relief'),
        ]

        for org, username in ngo_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': org,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'ngo',
                        'organization_name': org,
                        'phone': f'555-{random.randint(1000, 9999)}',
                        'latitude': 40.7128 + random.uniform(-0.05, 0.05),
                        'longitude': -74.0060 + random.uniform(-0.05, 0.05),
                        'verified': True,
                    }
                )
            ngos.append(user)

        # Create sample medicines
        medicines_data = [
            ('Aspirin', 'Aspirin 500mg tablets', 100, 'tablets'),
            ('Paracetamol', 'Paracetamol 500mg', 150, 'tablets'),
            ('Ibuprofen', 'Ibuprofen 400mg', 80, 'tablets'),
            ('Amoxicillin', 'Amoxicillin 250mg capsules', 50, 'capsules'),
            ('Antibiotics', 'Broad spectrum antibiotic', 30, 'bottles'),
            ('Vitamin D', 'Vitamin D3 supplement', 200, 'tablets'),
            ('Cough Syrup', 'Cough and cold relief', 25, 'bottles'),
            ('Antacid', 'Antacid tablets', 120, 'tablets'),
            ('Antihistamine', 'Allergy relief tablets', 90, 'tablets'),
            ('Insulin', 'Insulin vials', 10, 'vials'),
        ]

        medicines = []
        for name, desc, qty, unit in medicines_data:
            donor = random.choice(donors)
            medicine, created = Medicine.objects.get_or_create(
                name=name,
                donor=donor,
                defaults={
                    'description': desc,
                    'quantity': qty,
                    'unit': unit,
                    'expiry_date': date.today() + timedelta(days=random.randint(30, 365)),
                    'status': 'available',
                    'latitude': 40.7128 + random.uniform(-0.1, 0.1),
                    'longitude': -74.0060 + random.uniform(-0.1, 0.1),
                    'location_name': f'{donor.first_name}\'s Location',
                    'storage_condition': 'Room Temperature',
                }
            )
            medicines.append(medicine)

        # Create sample ratings
        for medicine in medicines:
            num_ratings = random.randint(2, 5)
            raters = random.sample(ngos, min(num_ratings, len(ngos)))
            
            for user in raters:
                rating_value = random.randint(3, 5)
                recommendation = "highly" if rating_value >= 4 else "reasonably"
                MedicineRating.objects.get_or_create(
                    medicine=medicine,
                    user=user,
                    defaults={
                        'rating': rating_value,
                        'review': f"Good quality medicine, {recommendation} recommended."
                    }
                )

        # Create sample donation requests
        for _ in range(10):
            medicine = random.choice(medicines)
            ngo = random.choice(ngos)
            
            DonationRequest.objects.get_or_create(
                medicine=medicine,
                ngo=ngo,
                defaults={
                    'status': random.choice(['pending', 'accepted', 'completed']),
                    'quantity_requested': random.randint(10, min(50, medicine.quantity)),
                    'message': 'We need this medicine for our clinic.',
                }
            )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(f'Created {len(donors)} donors')
        self.stdout.write(f'Created {len(ngos)} NGOs')
        self.stdout.write(f'Created {len(medicines)} medicines')
        self.stdout.write('\nTest Accounts:')
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Donor: username=john_smith, password=password123')
        self.stdout.write('NGO: username=red_cross, password=password123')
