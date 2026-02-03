from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from app.models import (
    UserProfile, Medicine, DonationRequest, PickupDelivery, Delivery, DeliveryBoy
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data and run a smoke test for pickup/delivery flows'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create users
            donor, _ = User.objects.get_or_create(username='smoke_donor', defaults={'email':'donor@example.com'})
            donor.set_password('testpass')
            donor.save()
            UserProfile.objects.update_or_create(user=donor, defaults={'role':'donor'})

            ngo, _ = User.objects.get_or_create(username='smoke_ngo', defaults={'email':'ngo@example.com'})
            ngo.set_password('testpass')
            ngo.save()
            UserProfile.objects.update_or_create(user=ngo, defaults={'role':'ngo'})

            # legacy delivery user creation removed

            # Create a medicine
            expiry = (timezone.now() + timedelta(days=365)).date()
            med, _ = Medicine.objects.get_or_create(
                donor=donor,
                name='SmokeTestMedicine',
                defaults={
                    'quantity': 10,
                    'expiry_date': expiry,
                }
            )

            # Create a donation request (accepted)
            req, _ = DonationRequest.objects.get_or_create(medicine=med, ngo=ngo, defaults={'status':'accepted'})
            req.status = 'accepted'
            req.save()

            # Create pickup_delivery
            pickup, created = PickupDelivery.objects.get_or_create(
                donation_request=req,
                defaults={
                    'donor': donor,
                    'ngo': ngo,
                    'medicine': med,
                    'status': 'pending',
                    'quantity_scheduled': 1
                }
            )

            self.stdout.write(self.style.SUCCESS('Smoke test data created:'))
            self.stdout.write(f'  donor={donor.username}, ngo={ngo.username}')
            self.stdout.write(f'  medicine={med.name} (id={med.id})')
            self.stdout.write(f'  donation_request id={req.id} status={req.status}')
            self.stdout.write(f'  pickup_delivery id={pickup.id} status={pickup.status}')
            # internal delivery entries removed

            # Create another donation + pickup to test claim flow
            req2, _ = DonationRequest.objects.get_or_create(medicine=med, ngo=ngo, defaults={'status':'accepted'})
            pickup2, _ = PickupDelivery.objects.get_or_create(donation_request=req2, defaults={'donor':donor,'ngo':ngo,'medicine':med,'quantity_scheduled':1,'status':'pending'})

            # claim simulation removed (external porter model used)
            self.stdout.write(self.style.SUCCESS('Claim simulation skipped (porter flow)'))
            self.stdout.write(f'  pickup2 id={pickup2.id}')

        self.stdout.write(self.style.SUCCESS('Smoke test finished.'))
