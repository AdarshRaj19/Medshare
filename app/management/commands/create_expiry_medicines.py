from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Medicine, MedicineCategory, MedicineSubcategory
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create medicines with expired and expiring-soon dates'

    def handle(self, *args, **options):
        # Get or create categories
        antibiotics_cat, _ = MedicineCategory.objects.get_or_create(
            name='Antibiotics',
            defaults={'description': 'Antibacterial medicines', 'icon': 'fa-pills', 'color': '#FF6B6B'}
        )
        
        painkillers_cat, _ = MedicineCategory.objects.get_or_create(
            name='Pain Relief',
            defaults={'description': 'Pain and fever management', 'icon': 'fa-heart', 'color': '#FF9FF3'}
        )
        
        respiratory_cat, _ = MedicineCategory.objects.get_or_create(
            name='Respiratory',
            defaults={'description': 'Cold, cough and respiratory', 'icon': 'fa-lungs', 'color': '#74B9FF'}
        )
        
        vitamins_cat, _ = MedicineCategory.objects.get_or_create(
            name='Vitamins & Supplements',
            defaults={'description': 'Vitamins and nutritional supplements', 'icon': 'fa-apple-alt', 'color': '#A29BFE'}
        )
        
        # Get donors
        donors = list(User.objects.filter(profile__role='donor')[:5])
        
        if not donors:
            self.stdout.write(self.style.ERROR('No donors found. Please create donors first.'))
            return
        
        today = timezone.now().date()
        
        # Already EXPIRED medicines (past dates)
        expired_medicines = [
            {
                'name': 'Expired Amoxicillin 250mg',
                'generic_name': 'Amoxicillin',
                'brand_name': 'Amoxil',
                'category': antibiotics_cat,
                'description': 'EXPIRED - Penicillin antibiotic (30 days expired)',
                'composition': 'Amoxicillin 250mg',
                'dosage_form': 'Tablet',
                'strength': '250mg',
                'quantity': 15,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Glaxo SmithKline',
                'batch_number': 'GSK2023001',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'EXPIRED - Do not use',
                'side_effects': 'N/A',
                'prescription_required': True,
                'expiry_date': today - timedelta(days=30),
                'donor_index': 0,
                'latitude': 28.6139,
                'longitude': 77.2090,
                'location_name': 'Delhi',
            },
            {
                'name': 'Expired Paracetamol 500mg',
                'generic_name': 'Paracetamol',
                'brand_name': 'Crocin',
                'category': painkillers_cat,
                'description': 'EXPIRED - Fever and pain reliever (15 days expired)',
                'composition': 'Paracetamol 500mg',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'quantity': 40,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Cipla Ltd',
                'batch_number': 'CIP2023045',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'EXPIRED - Do not use',
                'side_effects': 'N/A',
                'prescription_required': False,
                'expiry_date': today - timedelta(days=15),
                'donor_index': 1,
                'latitude': 19.0760,
                'longitude': 72.8777,
                'location_name': 'Mumbai',
            },
            {
                'name': 'Expired Cough Syrup',
                'generic_name': 'Dextromethorphan',
                'brand_name': 'Coughex',
                'category': respiratory_cat,
                'description': 'EXPIRED - Cough suppressant (45 days expired)',
                'composition': 'Dextromethorphan 10mg/5ml',
                'dosage_form': 'Syrup',
                'strength': '10mg/5ml',
                'quantity': 100,
                'unit': 'ml',
                'condition': 'opened',
                'manufacturer': 'Cipla Ltd',
                'batch_number': 'CIP2023056',
                'storage_condition': 'Below 30°C',
                'usage_instructions': 'EXPIRED - Do not use',
                'side_effects': 'N/A',
                'prescription_required': False,
                'expiry_date': today - timedelta(days=45),
                'donor_index': 2,
                'latitude': 12.9716,
                'longitude': 77.5946,
                'location_name': 'Bengaluru',
            },
            {
                'name': 'Expired Ibuprofen 400mg',
                'generic_name': 'Ibuprofen',
                'brand_name': 'Brufen',
                'category': painkillers_cat,
                'description': 'EXPIRED - Anti-inflammatory (7 days expired)',
                'composition': 'Ibuprofen 400mg',
                'dosage_form': 'Tablet',
                'strength': '400mg',
                'quantity': 20,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Abbott',
                'batch_number': 'ABB2023089',
                'storage_condition': 'Cool, dry place',
                'usage_instructions': 'EXPIRED - Do not use',
                'side_effects': 'N/A',
                'prescription_required': False,
                'expiry_date': today - timedelta(days=7),
                'donor_index': 3,
                'latitude': 23.1815,
                'longitude': 79.9864,
                'location_name': 'Indore',
            },
            {
                'name': 'Expired Vitamin C Syrup',
                'generic_name': 'Ascorbic Acid',
                'brand_name': 'Limcee',
                'category': vitamins_cat,
                'description': 'EXPIRED - Immune booster (60 days expired)',
                'composition': 'Ascorbic Acid 500mg/5ml',
                'dosage_form': 'Syrup',
                'strength': '500mg/5ml',
                'quantity': 150,
                'unit': 'ml',
                'condition': 'opened',
                'manufacturer': 'Abbott India',
                'batch_number': 'ABB2023123',
                'storage_condition': 'Cool, dry place',
                'usage_instructions': 'EXPIRED - Do not use',
                'side_effects': 'N/A',
                'prescription_required': False,
                'expiry_date': today - timedelta(days=60),
                'donor_index': 4,
                'latitude': 21.1458,
                'longitude': 79.0882,
                'location_name': 'Nagpur',
            },
        ]
        
        # EXPIRING SOON medicines (within 10 days)
        expiring_soon_medicines = [
            {
                'name': 'Expires Today - Ciprofloxacin 500mg',
                'generic_name': 'Ciprofloxacin',
                'brand_name': 'Ciproquin',
                'category': antibiotics_cat,
                'description': 'URGENT - Expires TODAY',
                'composition': 'Ciprofloxacin 500mg',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'quantity': 10,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Cipla Ltd',
                'batch_number': 'CIP2024INT001',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use immediately - expires today',
                'side_effects': 'Tendon rupture (rare)',
                'prescription_required': True,
                'expiry_date': today,
                'donor_index': 0,
                'latitude': 28.6139,
                'longitude': 77.2090,
                'location_name': 'Delhi',
            },
            {
                'name': 'Expires Tomorrow - Omeprazole 20mg',
                'generic_name': 'Omeprazole',
                'brand_name': 'Omez',
                'category': vitamins_cat,
                'description': 'URGENT - Expires TOMORROW',
                'composition': 'Omeprazole 20mg',
                'dosage_form': 'Capsule',
                'strength': '20mg',
                'quantity': 14,
                'unit': 'capsules',
                'condition': 'new',
                'manufacturer': 'Dr Reddys Labs',
                'batch_number': 'DRL2024INT002',
                'storage_condition': 'Below 25°C',
                'usage_instructions': 'Use urgently - expires tomorrow',
                'side_effects': 'Headache, nausea',
                'prescription_required': True,
                'expiry_date': today + timedelta(days=1),
                'donor_index': 1,
                'latitude': 19.0760,
                'longitude': 72.8777,
                'location_name': 'Mumbai',
            },
            {
                'name': 'Expires in 2 Days - Metformin 500mg',
                'generic_name': 'Metformin',
                'brand_name': 'Glucophage',
                'category': vitamins_cat,
                'description': 'URGENT - Expires in 2 DAYS',
                'composition': 'Metformin 500mg',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'quantity': 30,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Bristol Myers Squibb',
                'batch_number': 'BMS2024INT003',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use within 2 days',
                'side_effects': 'GI upset',
                'prescription_required': True,
                'expiry_date': today + timedelta(days=2),
                'donor_index': 2,
                'latitude': 12.9716,
                'longitude': 77.5946,
                'location_name': 'Bengaluru',
            },
            {
                'name': 'Expires in 3 Days - Antihistamine 10mg',
                'generic_name': 'Cetirizine',
                'brand_name': 'Alzental',
                'category': respiratory_cat,
                'description': 'URGENT - Expires in 3 DAYS',
                'composition': 'Cetirizine 10mg',
                'dosage_form': 'Tablet',
                'strength': '10mg',
                'quantity': 30,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Cipla Ltd',
                'batch_number': 'CIP2024INT004',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use within 3 days',
                'side_effects': 'Minimal',
                'prescription_required': False,
                'expiry_date': today + timedelta(days=3),
                'donor_index': 3,
                'latitude': 23.1815,
                'longitude': 79.9864,
                'location_name': 'Indore',
            },
            {
                'name': 'Expires in 5 Days - Aspirin 75mg',
                'generic_name': 'Acetylsalicylic Acid',
                'brand_name': 'Ecosprin',
                'category': painkillers_cat,
                'description': 'WARNING - Expires in 5 DAYS',
                'composition': 'Acetylsalicylic Acid 75mg',
                'dosage_form': 'Tablet',
                'strength': '75mg',
                'quantity': 100,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Micro Labs',
                'batch_number': 'MCL2024INT005',
                'storage_condition': 'Dry place',
                'usage_instructions': 'Use within 5 days',
                'side_effects': 'GI bleeding (rare)',
                'prescription_required': True,
                'expiry_date': today + timedelta(days=5),
                'donor_index': 4,
                'latitude': 21.1458,
                'longitude': 79.0882,
                'location_name': 'Nagpur',
            },
            {
                'name': 'Expires in 7 Days - Iron Supplement 65mg',
                'generic_name': 'Ferrous Sulphate',
                'brand_name': 'Feroglobin',
                'category': vitamins_cat,
                'description': 'WARNING - Expires in 7 DAYS',
                'composition': 'Ferrous Sulphate 65mg',
                'dosage_form': 'Tablet',
                'strength': '65mg',
                'quantity': 30,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Glaxo SmithKline',
                'batch_number': 'GSK2024INT006',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use within 7 days',
                'side_effects': 'Black stools',
                'prescription_required': True,
                'expiry_date': today + timedelta(days=7),
                'donor_index': 0,
                'latitude': 28.6139,
                'longitude': 77.2090,
                'location_name': 'Delhi',
            },
            {
                'name': 'Expires in 10 Days - Calcium Supplement 500mg',
                'generic_name': 'Calcium Carbonate',
                'brand_name': 'Shelcal',
                'category': vitamins_cat,
                'description': 'WARNING - Expires in 10 DAYS',
                'composition': 'Calcium Carbonate 500mg',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'quantity': 60,
                'unit': 'tablets',
                'condition': 'new',
                'manufacturer': 'Torrent Pharma',
                'batch_number': 'TOR2024INT007',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use within 10 days',
                'side_effects': 'Constipation',
                'prescription_required': False,
                'expiry_date': today + timedelta(days=10),
                'donor_index': 1,
                'latitude': 19.0760,
                'longitude': 72.8777,
                'location_name': 'Mumbai',
            },
            {
                'name': 'Expires in 9 Days - Antacid Suspension 200ml',
                'generic_name': 'Magnesium Hydroxide',
                'brand_name': 'Gelusil',
                'category': vitamins_cat,
                'description': 'WARNING - Expires in 9 DAYS',
                'composition': 'Magnesium Hydroxide 200mg per 5ml',
                'dosage_form': 'Suspension',
                'strength': '200ml',
                'quantity': 1,
                'unit': 'bottle',
                'condition': 'new',
                'manufacturer': 'GlaxoSmithKline',
                'batch_number': 'GSK2024INT008',
                'storage_condition': 'Room temperature',
                'usage_instructions': 'Use within 9 days',
                'side_effects': 'Constipation',
                'prescription_required': False,
                'expiry_date': today + timedelta(days=9),
                'donor_index': 2,
                'latitude': 12.9716,
                'longitude': 77.5946,
                'location_name': 'Bengaluru',
            },
            {
                'name': 'Expires in 6 Days - Antibiotic Cream 30g',
                'generic_name': 'Neomycin + Bacitracin',
                'brand_name': 'Sofraderm',
                'category': antibiotics_cat,
                'description': 'WARNING - Expires in 6 DAYS',
                'composition': 'Neomycin 500U/g + Bacitracin 400U/g',
                'dosage_form': 'Cream',
                'strength': '30g',
                'quantity': 2,
                'unit': 'tubes',
                'condition': 'new',
                'manufacturer': 'Glaxo SmithKline',
                'batch_number': 'GSK2024INT009',
                'storage_condition': 'Below 25°C',
                'usage_instructions': 'Use within 6 days',
                'side_effects': 'Local allergic reactions',
                'prescription_required': False,
                'expiry_date': today + timedelta(days=6),
                'donor_index': 3,
                'latitude': 23.1815,
                'longitude': 79.9864,
                'location_name': 'Indore',
            },
            {
                'name': 'Expires in 4 Days - Allergy Relief Syrup 100ml',
                'generic_name': 'Pheniramine Maleate',
                'brand_name': 'Avil',
                'category': respiratory_cat,
                'description': 'URGENT - Expires in 4 DAYS',
                'composition': 'Pheniramine Maleate 2mg per 5ml',
                'dosage_form': 'Syrup',
                'strength': '100ml',
                'quantity': 1,
                'unit': 'bottle',
                'condition': 'new',
                'manufacturer': 'Cipla Ltd',
                'batch_number': 'CIP2024INT010',
                'storage_condition': 'Below 30°C',
                'usage_instructions': 'Use within 4 days',
                'side_effects': 'Drowsiness',
                'prescription_required': False,
                'expiry_date': today + timedelta(days=4),
                'donor_index': 4,
                'latitude': 21.1458,
                'longitude': 79.0882,
                'location_name': 'Nagpur',
            },
        ]
        
        # Create EXPIRED medicines
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.ERROR('Creating EXPIRED Medicines'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        created_expired = 0
        manufacture_date = today - timedelta(days=365)
        
        for med_data in expired_medicines:
            try:
                donor = donors[med_data.pop('donor_index')]
                
                medicine, created = Medicine.objects.get_or_create(
                    donor=donor,
                    name=med_data['name'],
                    defaults={
                        **med_data,
                        'manufacture_date': manufacture_date,
                        'status': 'expired',
                        'verified_by_admin': True,
                        'rating': 0,
                        'rating_count': 0,
                    }
                )
                
                if created:
                    days_expired = (today - medicine.expiry_date).days
                    self.stdout.write(
                        self.style.ERROR(f'✗ EXPIRED: {medicine.name}')
                    )
                    self.stdout.write(f'  Expired {days_expired} days ago | Expiry: {medicine.expiry_date}')
                    created_expired += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⊙ Already exists: {medicine.name}')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating {med_data.get("name")}: {str(e)}')
                )
        
        # Create EXPIRING SOON medicines
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.WARNING('Creating EXPIRING SOON Medicines (within 10 days)'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        created_expiring = 0
        
        for med_data in expiring_soon_medicines:
            try:
                donor = donors[med_data.pop('donor_index')]
                expiry_date = med_data.pop('expiry_date')
                
                medicine, created = Medicine.objects.get_or_create(
                    donor=donor,
                    name=med_data['name'],
                    defaults={
                        **med_data,
                        'expiry_date': expiry_date,
                        'manufacture_date': today - timedelta(days=60),
                        'status': 'available',
                        'verified_by_admin': True,
                        'rating': 4.2,
                        'rating_count': 8,
                    }
                )
                
                if created:
                    days_left = (medicine.expiry_date - today).days
                    if days_left == 0:
                        self.stdout.write(
                            self.style.ERROR(f'🔴 EXPIRES TODAY: {medicine.name}')
                        )
                    elif days_left <= 3:
                        self.stdout.write(
                            self.style.WARNING(f'🟠 URGENT: {medicine.name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'🟡 WARNING: {medicine.name}')
                        )
                    self.stdout.write(f'  Expires in {days_left} day(s) | Expiry: {medicine.expiry_date}')
                    created_expiring += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⊙ Already exists: {medicine.name}')
                    )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating {med_data.get("name")}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {created_expired} expired medicines'))
        self.stdout.write(self.style.WARNING(f'✓ Created {created_expiring} expiring-soon medicines'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total: {created_expired + created_expiring} medicines with expiry tracking'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
