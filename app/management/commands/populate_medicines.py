from django.core.management.base import BaseCommand
from app.models import Medicine, MedicineCategory, User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populate 30 real medicines with random donors and categories.'

    def handle(self, *args, **options):
        categories = list(MedicineCategory.objects.all())
        donors = list(User.objects.filter(profile__role='donor'))
        names = [
            'Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Ciprofloxacin', 'Azithromycin',
            'Metformin', 'Amlodipine', 'Atorvastatin', 'Omeprazole', 'Cetirizine',
            'Doxycycline', 'Levothyroxine', 'Losartan', 'Gabapentin', 'Hydrochlorothiazide',
            'Simvastatin', 'Pantoprazole', 'Prednisone', 'Clopidogrel', 'Escitalopram',
            'Sertraline', 'Tamsulosin', 'Rosuvastatin', 'Lisinopril', 'Metoprolol',
            'Alprazolam', 'Fluoxetine', 'Cefixime', 'Montelukast', 'Diclofenac'
        ]
        created = 0
        for i in range(30):
            med = Medicine.objects.create(
                name=names[i],
                quantity=random.randint(5, 50),
                category=random.choice(categories) if categories else None,
                donor=random.choice(donors) if donors else None,
                expiry_date=timezone.now().date().replace(year=timezone.now().year+1),
                status='available'
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created} medicines.'))
