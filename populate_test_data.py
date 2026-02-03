"""
Test Data Population Script
Creates realistic test data for all user roles and features
"""

import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from app.models import (
    UserProfile, MedicineCategory, MedicineSubcategory, Medicine,
    DonationRequest, EmergencyAlert, DeliveryBoy, Delivery, PickupDelivery
)

def create_test_data():
    """Create comprehensive test data for demonstration"""
    
    print("\n" + "="*70)
    print(" CREATING TEST DATA FOR ALL FEATURES")
    print("="*70 + "\n")
    
    # 1. Create Categories
    print("✓ Creating Medicine Categories...")
    categories_data = [
        ('Painkillers', 'Pain relief medications'),
        ('Antibiotics', 'Antibacterial medicines'),
        ('Vitamins', 'Vitamin supplements'),
        ('Cold & Cough', 'Cold and cough remedies'),
        ('Digestive', 'Digestive system medicines'),
        ('Cardiac', 'Heart and cardiovascular medicines'),
        ('Diabetes', 'Diabetes management medicines'),
        ('Respiratory', 'Respiratory system medicines'),
    ]
    
    categories = {}
    for name, desc in categories_data:
        cat, created = MedicineCategory.objects.get_or_create(
            name=name,
            defaults={'description': desc, 'active': True}
        )
        categories[name] = cat
        if created:
            print(f"  ✓ Created: {name}")
    
    # 2. Create Subcategories
    print("\n✓ Creating Medicine Subcategories...")
    subcategories_data = [
        ('Painkillers', ['Tablets', 'Capsules', 'Syrups']),
        ('Antibiotics', ['Tablets', 'Injections', 'Creams']),
        ('Vitamins', ['Tablets', 'Capsules', 'Syrups']),
    ]
    
    for cat_name, subcat_names in subcategories_data:
        if cat_name in categories:
            for subcat_name in subcat_names:
                subcat, created = MedicineSubcategory.objects.get_or_create(
                    category=categories[cat_name],
                    name=subcat_name,
                    defaults={'active': True}
                )
                if created:
                    print(f"  ✓ {cat_name} → {subcat_name}")
    
    # 3. Create Test Users
    print("\n✓ Creating Test Users...")
    users_data = [
        ('donor1', 'Donor User 1', 'donor', '9876543210'),
        ('ngo1', 'NGO User 1', 'ngo', '9876543211'),
        ('delivery1', 'Delivery Partner 1', 'donor', '9876543212'),
        ('volunteer1', 'Volunteer User 1', 'donor', '9876543213'),
        ('admin1', 'Admin User', 'admin', '9876543214'),
    ]
    
    users = {}
    for username, full_name, role, phone in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': full_name.split()[0],
                'last_name': full_name.split()[1] if len(full_name.split()) > 1 else '',
                'email': f'{username}@medshare.local'
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            
            # Create UserProfile
            profile, p_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'phone': phone,
                    'latitude': 28.7041 + (len(users) * 0.01),
                    'longitude': 77.1025 + (len(users) * 0.01),
                }
            )
            print(f"  ✓ Created {role}: {username}")
        
        users[username] = user
    
    # 4. Create Test Medicines
    print("\n✓ Creating Test Medicines...")
    medicines_data = [
        ('Paracetamol 500mg', 'Paracetamol', 'Crocin', 'Painkillers', 
         10, '2026-12-31', 'Tablet'),
        ('Amoxicillin 500mg', 'Amoxicillin', 'Amoxil', 'Antibiotics',
         5, '2026-11-30', 'Capsule'),
        ('Vitamin C 1000mg', 'Ascorbic Acid', 'C500', 'Vitamins',
         20, '2027-06-30', 'Tablet'),
        ('Cough Syrup', 'Dextromethorphan', 'CodelX', 'Cold & Cough',
         3, '2026-08-31', 'Syrup'),
    ]
    
    medicines = []
    for name, generic, brand, category, qty, expiry, dosage in medicines_data:
        if category in categories:
            med, created = Medicine.objects.get_or_create(
                name=name,
                donor=users['donor1'],
                defaults={
                    'brand_name': brand,
                    'generic_name': generic,
                    'category': categories[category],
                    'quantity': qty,
                    'unit': 'tablets' if dosage == 'Tablet' else 'units',
                    'condition': 'new',
                    'expiry_date': expiry,
                    'dosage_form': dosage,
                    'strength': '500mg' if '500' in name else '1000mg',
                    'status': 'available',
                    'verified_by_admin': True,
                    'latitude': 28.7041,
                    'longitude': 77.1025,
                    'location_name': 'Delhi, India'
                }
            )
            if created:
                print(f"  ✓ Created: {name} ({qty} {dosage}s)")
            medicines.append(med)
    
    # 5. Create Emergency Alert
    print("\n✓ Creating Emergency Alert...")
    if 'ngo1' in users and 'Painkillers' in categories:
        alert, created = EmergencyAlert.objects.get_or_create(
            ngo=users['ngo1'],
            medicine_category=categories['Painkillers'],
            defaults={
                'medicine_name': 'Paracetamol',
                'quantity_needed': 50,
                'unit': 'tablets',
                'priority': 'high',
                'description': 'Urgent need for paracetamol for emergency ward',
                'patient_count': 10,
                'deadline': timezone.now() + timedelta(hours=6),
                'latitude': 28.7041,
                'longitude': 77.1025,
                'location_name': 'Emergency Ward, Delhi',
                'is_active': True
            }
        )
        if created:
            print(f"  ✓ Created: Emergency Alert for {alert.medicine_name}")
    
    # 6. Delivery partner / delivery boy creation skipped (external porter model preferred)
    
    # 7. Create Donation Request
    print("\n✓ Creating Donation Requests...")
    donation_req = None
    if 'ngo1' in users and medicines:
        donation_req, created = DonationRequest.objects.get_or_create(
            medicine=medicines[0],
            ngo=users['ngo1'],
            defaults={
                'quantity_requested': 5,
                'status': 'pending',
                'message': 'Request for Paracetamol for our clinic'
            }
        )
        if created:
            print(f"  ✓ Created: Donation Request by NGO")
    
    # 8. Create Pickup Delivery
    print("\n✓ Creating Pickup/Delivery Records...")
    if 'ngo1' in users and medicines and donation_req:
        pickup, created = PickupDelivery.objects.get_or_create(
            donation_request=donation_req,
            donor=users['donor1'],
            ngo=users['ngo1'],
            medicine=medicines[0],
            defaults={
                'status': 'pending',
                'quantity_scheduled': 5,
                'quantity_picked_up': 0,
                'quantity_delivered': 0,
                'scheduled_pickup_date': timezone.now() + timedelta(days=1),
            }
        )
        if created:
            print(f"  ✓ Created: Pickup/Delivery Record")
    
    print("\n" + "="*70)
    print(" TEST DATA CREATION COMPLETE ✅")
    print("="*70)
    print(f"\n📊 Created Data Summary:")
    print(f"   ✓ Categories: {MedicineCategory.objects.count()}")
    print(f"   ✓ Subcategories: {MedicineSubcategory.objects.count()}")
    print(f"   ✓ Users: {User.objects.count()}")
    print(f"   ✓ Medicines: {Medicine.objects.count()}")
    print(f"   ✓ Emergency Alerts: {EmergencyAlert.objects.count()}")
    print(f"   ✓ Donation Requests: {DonationRequest.objects.count()}")
    # internal delivery boy count removed
    print(f"   ✓ Pickup/Deliveries: {PickupDelivery.objects.count()}")
    print("\n" + "="*70)

if __name__ == '__main__':
    create_test_data()
