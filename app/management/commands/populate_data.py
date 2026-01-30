from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import (
    Medicine, UserProfile, DonationRequest, MedicineRating,
    MedicineCategory, MedicineSubcategory, EmergencyAlert,
    BulkDonationRequest, BulkDonationItem, MedicineVerification,
    FAQ, Testimonial
)
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create medicine categories
        categories_data = [
            ('Pain Relief', 'Painkillers and analgesics', 'fas fa-pills', '#e74c3c'),
            ('Antibiotics', 'Antibiotic medications', 'fas fa-bacteria', '#27ae60'),
            ('Cardiovascular', 'Heart and blood pressure medicines', 'fas fa-heartbeat', '#e67e22'),
            ('Respiratory', 'Lung and breathing medicines', 'fas fa-lungs', '#3498db'),
            ('Diabetes', 'Diabetes management medicines', 'fas fa-syringe', '#9b59b6'),
            ('Vitamins & Supplements', 'Vitamins and nutritional supplements', 'fas fa-apple-alt', '#f39c12'),
            ('First Aid', 'Basic first aid supplies', 'fas fa-first-aid', '#16a085'),
            ('Mental Health', 'Mental health medications', 'fas fa-brain', '#8e44ad'),
        ]

        categories = []
        for name, desc, icon, color in categories_data:
            category, created = MedicineCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'icon': icon,
                    'color': color,
                }
            )
            categories.append(category)

        # Create subcategories
        subcategories_data = [
            ('Pain Relief', 'NSAIDs', 'Non-steroidal anti-inflammatory drugs'),
            ('Pain Relief', 'Opioids', 'Opioid pain medications'),
            ('Antibiotics', 'Penicillins', 'Penicillin antibiotics'),
            ('Antibiotics', 'Cephalosporins', 'Cephalosporin antibiotics'),
            ('Cardiovascular', 'Beta Blockers', 'Beta blocker medications'),
            ('Cardiovascular', 'ACE Inhibitors', 'ACE inhibitor medications'),
            ('Diabetes', 'Insulin', 'Insulin medications'),
            ('Diabetes', 'Oral Hypoglycemics', 'Oral diabetes medications'),
        ]

        for cat_name, sub_name, sub_desc in subcategories_data:
            try:
                category = MedicineCategory.objects.get(name=cat_name)
                MedicineSubcategory.objects.get_or_create(
                    category=category,
                    name=sub_name,
                    defaults={'description': sub_desc}
                )
            except MedicineCategory.DoesNotExist:
                pass

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

        # Create sample medicines with enhanced data
        medicines_data = [
            ('Aspirin', 'Bayer Aspirin', 'Acetylsalicylic Acid', 'Pain Relief', 'NSAIDs', 'Tablet', '500mg', 'Acetylsalicylic acid', 100, 'tablets', 'Bayer', False),
            ('Paracetamol', 'Tylenol', 'Paracetamol', 'Pain Relief', 'NSAIDs', 'Tablet', '500mg', 'Paracetamol', 150, 'tablets', 'Johnson & Johnson', False),
            ('Ibuprofen', 'Advil', 'Ibuprofen', 'Pain Relief', 'NSAIDs', 'Tablet', '400mg', 'Ibuprofen', 80, 'tablets', 'Pfizer', False),
            ('Amoxicillin', 'Amoxil', 'Amoxicillin', 'Antibiotics', 'Penicillins', 'Capsule', '250mg', 'Amoxicillin trihydrate', 50, 'capsules', 'GSK', True),
            ('Azithromycin', 'Zithromax', 'Azithromycin', 'Antibiotics', 'Macrolides', 'Tablet', '500mg', 'Azithromycin', 30, 'tablets', 'Pfizer', True),
            ('Vitamin D3', 'Nature Made', 'Cholecalciferol', 'Vitamins & Supplements', 'Vitamins', 'Tablet', '1000IU', 'Vitamin D3', 200, 'tablets', 'Nature Made', False),
            ('Cough Syrup', 'Robitussin', 'Dextromethorphan', 'Respiratory', 'Cough Suppressants', 'Syrup', '100ml', 'Dextromethorphan and guaifenesin', 25, 'bottles', 'Wyeth', False),
            ('Antacid', 'Tums', 'Calcium Carbonate', 'First Aid', 'Digestive Health', 'Tablet', '500mg', 'Calcium carbonate', 120, 'tablets', 'GlaxoSmithKline', False),
            ('Loratadine', 'Claritin', 'Loratadine', 'First Aid', 'Antihistamines', 'Tablet', '10mg', 'Loratadine', 90, 'tablets', 'Bayer', False),
            ('Insulin', 'Humalog', 'Insulin Lispro', 'Diabetes', 'Insulin', 'Vial', '10ml', 'Insulin lispro', 10, 'vials', 'Eli Lilly', True),
        ]

        medicines = []
        for name, brand, generic, cat_name, sub_name, dosage_form, strength, composition, qty, unit, manufacturer, prescription in medicines_data:
            donor = random.choice(donors)
            try:
                category = MedicineCategory.objects.get(name=cat_name)
                subcategory = MedicineSubcategory.objects.filter(category=category, name=sub_name).first()
            except MedicineCategory.DoesNotExist:
                category = None
                subcategory = None
            
            medicine, created = Medicine.objects.get_or_create(
                name=name,
                donor=donor,
                defaults={
                    'brand_name': brand,
                    'generic_name': generic,
                    'category': category,
                    'subcategory': subcategory,
                    'description': f'{brand} {name} - {generic}',
                    'dosage_form': dosage_form,
                    'strength': strength,
                    'composition': composition,
                    'quantity': qty,
                    'unit': unit,
                    'manufacturer': manufacturer,
                    'expiry_date': date.today() + timedelta(days=random.randint(30, 365)),
                    'manufacture_date': date.today() - timedelta(days=random.randint(30, 180)),
                    'batch_number': f'BATCH{random.randint(10000, 99999)}',
                    'condition': random.choice(['new', 'opened']),
                    'storage_condition': 'Store at room temperature',
                    'usage_instructions': 'Take as directed by physician',
                    'side_effects': 'Consult physician for side effects',
                    'contraindications': 'Consult physician before use',
                    'prescription_required': prescription,
                    'pickup_available': True,
                    'delivery_available': random.choice([True, False]),
                    'status': 'available',
                    'latitude': 40.7128 + random.uniform(-0.1, 0.1),
                    'longitude': -74.0060 + random.uniform(-0.1, 0.1),
                    'location_name': f'{donor.first_name}\'s Location',
                    'verified_by_admin': random.choice([True, False]),
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

        # Create emergency alerts
        emergency_medicines = [
            ('Insulin', 'Diabetes', 'Critical shortage of insulin for diabetic patients'),
            ('Amoxicillin', 'Antibiotics', 'Urgent need for pediatric antibiotics'),
            ('Paracetamol', 'Pain Relief', 'High fever outbreak in community'),
            ('Azithromycin', 'Antibiotics', 'Respiratory infection surge'),
        ]

        for med_name, cat_name, desc in emergency_medicines:
            try:
                category = MedicineCategory.objects.get(name=cat_name)
                ngo = random.choice(ngos)
                EmergencyAlert.objects.get_or_create(
                    ngo=ngo,
                    medicine_name=med_name,
                    defaults={
                        'medicine_category': category,
                        'quantity_needed': random.randint(50, 200),
                        'unit': 'units',
                        'priority': random.choice(['high', 'critical']),
                        'description': desc,
                        'patient_count': random.randint(20, 100),
                        'deadline': date.today() + timedelta(days=random.randint(3, 14)),
                        'latitude': ngo.profile.latitude,
                        'longitude': ngo.profile.longitude,
                        'location_name': ngo.profile.organization_name,
                    }
                )
            except MedicineCategory.DoesNotExist:
                pass

        # Create bulk donation requests
        for i in range(3):
            ngo = random.choice(ngos)
            bulk_request, created = BulkDonationRequest.objects.get_or_create(
                ngo=ngo,
                title=f'Monthly Medicine Supply - {ngo.profile.organization_name}',
                defaults={
                    'description': 'Monthly requirement for essential medicines',
                    'status': 'submitted',
                    'priority': random.choice(['medium', 'high']),
                    'submitted_at': date.today(),
                }
            )
            
            if created:
                # Add items to bulk request
                for _ in range(random.randint(3, 6)):
                    category = random.choice(categories)
                    BulkDonationItem.objects.create(
                        bulk_request=bulk_request,
                        medicine_category=category,
                        medicine_name=f'Sample {category.name} Medicine',
                        quantity_requested=random.randint(20, 100),
                        unit='units',
                        urgency_level=random.choice(['medium', 'high']),
                        notes=f'Needed for {ngo.profile.organization_name} clinic',
                    )

        # Create FAQs
        faqs_data = [
            ('How do I donate medicine?', 'To donate medicine, create an account as a donor, add your medicine details including expiry date and condition, and make it available for NGOs to request.', 'donation'),
            ('What types of medicine can I donate?', 'You can donate unexpired, properly stored medicines. Prescription medicines require verification. Always check expiry dates and storage conditions.', 'donation'),
            ('How do NGOs request medicine?', 'NGOs can browse available medicines, view details, and submit requests. They can also create emergency alerts for urgent needs.', 'request'),
            ('Is my donation information confidential?', 'Yes, donor information is kept confidential. NGOs only see medicine details and pickup/delivery options.', 'safety'),
            ('How is medicine quality verified?', 'All medicines go through admin verification. Donors should provide accurate information about expiry dates and storage conditions.', 'safety'),
            ('Can I track my donation?', 'Yes, you can track the status of your donated medicines through your donor dashboard.', 'technical'),
        ]

        for question, answer, category in faqs_data:
            FAQ.objects.get_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'category': category,
                    'active': True,
                }
            )

        # Create testimonials
        testimonials_data = [
            ('Dr. Sarah Mitchell', 'donor', 'City Hospital', 'MedShare has revolutionized how we access essential medicines for our patients. The platform is reliable and user-friendly.'),
            ('John Rodriguez', 'donor', 'Individual Donor', 'I\'m proud to donate my unused medicines. Knowing they help those in need makes every donation worthwhile.'),
            ('Maria Gonzalez', 'ngo', 'Hope Foundation', 'This platform has helped us reach more donors and get medicines to communities that need them most.'),
            ('Dr. Ahmed Hassan', 'ngo', 'Medical Relief International', 'The emergency alert system is a game-changer for urgent medical situations. Highly recommended!'),
        ]

        for name, role, org, message in testimonials_data:
            Testimonial.objects.get_or_create(
                name=name,
                defaults={
                    'role': role,
                    'message': message,
                    'approved': True,
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
