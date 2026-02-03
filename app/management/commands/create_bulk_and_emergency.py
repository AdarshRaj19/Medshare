from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import (
    BulkDonationRequest, BulkDonationItem, EmergencyAlert, EmergencyAlertResponse,
    MedicineCategory, MedicineInventory
)
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create bulk requests, emergency alerts, and emergency responses'

    def handle(self, *args, **options):
        # Get users
        donors = list(User.objects.filter(profile__role='donor')[:8])
        ngos = list(User.objects.filter(profile__role='ngo')[:10])
        
        if not donors or not ngos:
            self.stdout.write(self.style.ERROR('No donors or NGOs found.'))
            return
        
        # Get categories
        categories = list(MedicineCategory.objects.all()[:5])
        
        if not categories:
            self.stdout.write(self.style.ERROR('No medicine categories found.'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('Creating Bulk Requests & Emergency Alerts'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # ===== 1. CREATE BULK DONATION REQUESTS =====
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Bulk Donation Requests...'))
        
        bulk_requests_data = [
            {
                'title': 'Medical Camp Supplies - Vaccination Drive',
                'description': 'We are organizing a mass vaccination drive in rural areas. Need various medicines for pre/post vaccination care.',
                'priority': 'urgent',
                'items': [
                    ('Antibiotics', 'Amoxicillin', 500, 'tablets'),
                    ('Pain Relief', 'Paracetamol', 1000, 'tablets'),
                    ('Respiratory', 'Cough Syrup', 50, 'bottles'),
                ]
            },
            {
                'title': 'Seasonal Flu Preparedness Stock',
                'description': 'Preparing for flu season. Need antiviral and supportive medicines.',
                'priority': 'high',
                'items': [
                    ('Respiratory', 'Antihistamine', 300, 'tablets'),
                    ('Pain Relief', 'Ibuprofen', 400, 'tablets'),
                    ('Digestive Health', 'Antacid', 200, 'tablets'),
                ]
            },
            {
                'title': 'Chronic Disease Management Program',
                'description': 'Long-term care program for diabetes and hypertension patients.',
                'priority': 'high',
                'items': [
                    ('Vitamins & Supplements', 'Metformin', 200, 'tablets'),
                    ('Vitamins & Supplements', 'Iron Supplement', 300, 'tablets'),
                ]
            },
            {
                'title': 'Emergency Medical Supply Restocking',
                'description': 'Critical shortage in our emergency ward. Need immediate supplies.',
                'priority': 'urgent',
                'items': [
                    ('Antibiotics', 'Ciprofloxacin', 100, 'tablets'),
                    ('Antibiotics', 'Eye Drops', 50, 'bottles'),
                    ('Pain Relief', 'Aspirin', 200, 'tablets'),
                ]
            },
            {
                'title': 'Community Health Initiative - Monthly Supply',
                'description': 'Regular supply for our ongoing community health programs.',
                'priority': 'medium',
                'items': [
                    ('Vitamins & Supplements', 'Vitamin C', 500, 'tablets'),
                    ('Digestive Health', 'Antacid', 150, 'tablets'),
                ]
            },
            {
                'title': 'Pediatric Clinic Medicines Stock',
                'description': 'Medicines specifically for children in our pediatric clinic.',
                'priority': 'high',
                'items': [
                    ('Respiratory', 'Cough Syrup', 100, 'bottles'),
                    ('Pain Relief', 'Paracetamol', 500, 'tablets'),
                    ('Vitamins & Supplements', 'Multivitamin', 100, 'bottles'),
                ]
            },
        ]
        
        bulk_count = 0
        bulk_items_count = 0
        completed_bulks = []
        pending_bulks = []
        
        for idx, bulk_data in enumerate(bulk_requests_data):
            ngo = ngos[idx % len(ngos)]
            status = random.choices(['submitted', 'partial', 'completed'], weights=[0.3, 0.4, 0.3])[0]
            
            bulk_request, created = BulkDonationRequest.objects.get_or_create(
                ngo=ngo,
                title=bulk_data['title'],
                defaults={
                    'description': bulk_data['description'],
                    'status': status,
                    'priority': bulk_data['priority'],
                    'submitted_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                }
            )
            
            if created:
                bulk_count += 1
                
                # Create items
                for category_name, medicine_name, quantity, unit in bulk_data['items']:
                    category = next((c for c in categories if c.name == category_name), categories[0])
                    urgency = 'critical' if bulk_data['priority'] == 'urgent' else 'high' if bulk_data['priority'] == 'high' else 'medium'
                    
                    fulfilled = 0
                    if status == 'completed':
                        fulfilled = quantity
                    elif status == 'partial':
                        fulfilled = int(quantity * random.uniform(0.4, 0.9))
                    
                    item, _ = BulkDonationItem.objects.get_or_create(
                        bulk_request=bulk_request,
                        medicine_name=medicine_name,
                        defaults={
                            'medicine_category': category,
                            'quantity_requested': quantity,
                            'unit': unit,
                            'urgency_level': urgency,
                            'fulfilled_quantity': fulfilled,
                            'status': 'fulfilled' if fulfilled == quantity else 'partial' if fulfilled > 0 else 'pending',
                            'notes': random.choice([
                                'High demand from patients',
                                'For upcoming medical camp',
                                'Critical shortage',
                                'Regular stock replenishment',
                                'Emergency supply needed',
                            ])
                        }
                    )
                    bulk_items_count += 1
                
                # Track status
                if status == 'completed':
                    completed_bulks.append(bulk_request)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ COMPLETED: {bulk_request.title}'))
                else:
                    pending_bulks.append(bulk_request)
                    self.stdout.write(self.style.WARNING(f'  ⏳ {status.upper()}: {bulk_request.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {bulk_count} bulk requests with {bulk_items_count} items'))
        self.stdout.write(self.style.SUCCESS(f'  ├─ Completed: {len(completed_bulks)}'))
        self.stdout.write(self.style.SUCCESS(f'  └─ Pending: {len(pending_bulks)}'))
        
        # ===== 2. CREATE EMERGENCY ALERTS =====
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Emergency Alerts...'))
        
        emergency_data = [
            {
                'medicine_name': 'Oxygen Cylinders',
                'category_name': 'Respiratory',
                'quantity': 50,
                'unit': 'cylinders',
                'priority': 'critical',
                'description': 'COVID-19 outbreak in our area. Critical shortage of oxygen cylinders.',
                'patient_count': 120,
                'help_received': True,
            },
            {
                'medicine_name': 'Antibiotics - Cephalosporin',
                'category_name': 'Antibiotics',
                'quantity': 200,
                'unit': 'vials',
                'priority': 'critical',
                'description': 'Infection outbreak at our trauma center. Urgent need for broad-spectrum antibiotics.',
                'patient_count': 45,
                'help_received': True,
            },
            {
                'medicine_name': 'Insulin Injections',
                'category_name': 'Vitamins & Supplements',
                'quantity': 300,
                'unit': 'vials',
                'priority': 'critical',
                'description': 'Diabetic patients in emergency condition. Critical insulin shortage.',
                'patient_count': 60,
                'help_received': False,
            },
            {
                'medicine_name': 'Anticonvulsants',
                'category_name': 'Antibiotics',
                'quantity': 150,
                'unit': 'tablets',
                'priority': 'high',
                'description': 'Epilepsy ward facing shortage. Patients at risk without immediate supply.',
                'patient_count': 30,
                'help_received': True,
            },
            {
                'medicine_name': 'Blood Pressure Medication',
                'category_name': 'Vitamins & Supplements',
                'quantity': 500,
                'unit': 'tablets',
                'priority': 'high',
                'description': 'Hypertension patients unable to get medications. Risk of complications.',
                'patient_count': 100,
                'help_received': False,
            },
            {
                'medicine_name': 'Cardiac Medications',
                'category_name': 'Digestive Health',
                'quantity': 100,
                'unit': 'tablets',
                'priority': 'critical',
                'description': 'Heart patients in immediate danger due to medication shortage.',
                'patient_count': 25,
                'help_received': True,
            },
            {
                'medicine_name': 'Stroke Recovery Medications',
                'category_name': 'Respiratory',
                'quantity': 200,
                'unit': 'tablets',
                'priority': 'high',
                'description': 'Post-stroke patients need immediate medication for recovery.',
                'patient_count': 40,
                'help_received': False,
            },
            {
                'medicine_name': 'Burn Treatment Antibiotics',
                'category_name': 'Antibiotics',
                'quantity': 50,
                'unit': 'tubes',
                'priority': 'critical',
                'description': 'Industrial accident victims with burns. Risk of infection without antibiotics.',
                'patient_count': 8,
                'help_received': True,
            },
        ]
        
        emergency_count = 0
        resolved_emergencies = []
        pending_emergencies = []
        response_count = 0
        
        for idx, emerg_data in enumerate(emergency_data):
            ngo = ngos[idx % len(ngos)]
            category = next((c for c in categories if c.name == emerg_data['category_name']), categories[0])
            
            deadline = timezone.now() + timedelta(hours=random.randint(4, 48))
            
            alert, created = EmergencyAlert.objects.get_or_create(
                ngo=ngo,
                medicine_name=emerg_data['medicine_name'],
                defaults={
                    'medicine_category': category,
                    'quantity_needed': emerg_data['quantity'],
                    'unit': emerg_data['unit'],
                    'priority': emerg_data['priority'],
                    'description': emerg_data['description'],
                    'patient_count': emerg_data['patient_count'],
                    'deadline': deadline,
                    'latitude': ngo.profile.latitude,
                    'longitude': ngo.profile.longitude,
                    'location_name': ngo.profile.organization_name,
                    'is_active': not emerg_data['help_received'],
                    'resolved_at': timezone.now() - timedelta(hours=random.randint(1, 24)) if emerg_data['help_received'] else None,
                }
            )
            
            if created:
                emergency_count += 1
                
                if emerg_data['help_received']:
                    resolved_emergencies.append(alert)
                    emoji = '✓'
                else:
                    pending_emergencies.append(alert)
                    emoji = '🔴'
                
                self.stdout.write(f'  {emoji} {alert.priority.upper()}: {alert.medicine_name} - {alert.patient_count} patients affected')
                
                # Create responses if help was received
                if emerg_data['help_received']:
                    num_responses = random.randint(1, 3)
                    for _ in range(num_responses):
                        donor = random.choice(donors)
                        response, resp_created = EmergencyAlertResponse.objects.get_or_create(
                            alert=alert,
                            donor=donor,
                            defaults={
                                'quantity_offered': random.randint(int(emerg_data['quantity'] * 0.3), int(emerg_data['quantity'] * 0.7)),
                                'message': random.choice([
                                    'We can provide this medicine immediately',
                                    'Our pharmacy can fulfill this request',
                                    'We have stock available and can deliver ASAP',
                                    'Ready to help. Can arrange immediate supply',
                                    'Our hospital can provide these medicines urgently',
                                ]),
                                'accepted': True,
                            }
                        )
                        if resp_created:
                            response_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {emergency_count} emergency alerts'))
        self.stdout.write(self.style.SUCCESS(f'  ├─ Resolved (Help Received): {len(resolved_emergencies)}'))
        self.stdout.write(self.style.SUCCESS(f'  ├─ Pending (Still Seeking Help): {len(pending_emergencies)}'))
        self.stdout.write(self.style.SUCCESS(f'  └─ Total Donor Responses: {response_count}'))
        
        # ===== 3. CREATE MEDICINE INVENTORY FOR NGOs =====
        self.stdout.write(self.style.SUCCESS('\n▶ Creating NGO Medicine Inventory...'))
        
        inventory_count = 0
        
        for ngo in ngos[:6]:
            for category in categories[:4]:
                medicines = [
                    'Paracetamol', 'Aspirin', 'Vitamin C', 'Antacid', 'Antibiotics',
                    'Cough Syrup', 'Antihistamine', 'Calcium', 'Iron Supplement', 'Ibuprofen'
                ]
                medicine_name = random.choice(medicines)
                current_stock = random.randint(10, 500)
                minimum_stock = random.randint(5, 100)
                
                inventory, created = MedicineInventory.objects.get_or_create(
                    ngo=ngo,
                    medicine_category=category,
                    medicine_name=medicine_name,
                    defaults={
                        'current_stock': current_stock,
                        'minimum_stock_level': minimum_stock,
                        'unit': 'tablets',
                        'auto_reorder': random.random() < 0.4,
                    }
                )
                
                if created:
                    inventory_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {inventory_count} inventory records for NGOs'))
        
        # ===== SUMMARY =====
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✓ BULK REQUESTS & EMERGENCY ALERTS COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS(f'\n📦 BULK DONATION REQUESTS: {bulk_count}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ Items Listed: {bulk_items_count}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ Completed: {len(completed_bulks)}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ Partially Fulfilled: {len(pending_bulks)}'))
        self.stdout.write(self.style.SUCCESS(f'   └─ Status: Mix of active and completed'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🆘 EMERGENCY ALERTS: {emergency_count}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ RESOLVED (Help Received): {len(resolved_emergencies)}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ PENDING (Still Seeking): {len(pending_emergencies)}'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ Donor Responses: {response_count}'))
        self.stdout.write(self.style.SUCCESS(f'   └─ Critical Cases: {len([e for e in (resolved_emergencies + pending_emergencies) if e.priority == "critical"])}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 NGO INVENTORY: {inventory_count} records'))
        self.stdout.write(self.style.SUCCESS(f'   ├─ Tracked for: {len(ngos[:6])} NGOs'))
        self.stdout.write(self.style.SUCCESS(f'   └─ Auto-reorder enabled for some'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🎉 YOUR WEBSITE NOW SHOWS:'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('✓ Bulk requests from NGOs for medical camps'))
        self.stdout.write(self.style.SUCCESS('✓ Emergency alerts for critical situations'))
        self.stdout.write(self.style.SUCCESS('✓ Some emergencies RESOLVED - donors helping'))
        self.stdout.write(self.style.SUCCESS('✓ Some emergencies PENDING - still seeking help'))
        self.stdout.write(self.style.SUCCESS('✓ Donor responses showing community engagement'))
        self.stdout.write(self.style.SUCCESS('✓ NGO inventory management system active'))
        self.stdout.write(self.style.SUCCESS('✓ Real-time tracking of medical supply needs'))
        self.stdout.write(self.style.SUCCESS('\n' + '='*80 + '\n'))
