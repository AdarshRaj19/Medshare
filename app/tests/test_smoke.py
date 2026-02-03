from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from app.models import (
    UserProfile, Medicine, DonationRequest, PickupDelivery
)

User = get_user_model()

class SmokeFlowTests(TestCase):
    def setUp(self):
        # create users
        self.donor = User.objects.create_user(username='test_donor', password='testpass')
        UserProfile.objects.update_or_create(user=self.donor, defaults={'role':'donor'})

        self.ngo = User.objects.create_user(username='test_ngo', password='testpass')
        UserProfile.objects.update_or_create(user=self.ngo, defaults={'role':'ngo'})

        # delivery system removed; no delivery boy created

        # medicine
        expiry = (timezone.now() + timedelta(days=365)).date()
        self.med = Medicine.objects.create(donor=self.donor, name='TestMed', quantity=5, expiry_date=expiry)

    def test_pickup_and_delivery_creation_and_claim(self):
        # create donation request accepted
        req = DonationRequest.objects.create(medicine=self.med, ngo=self.ngo, status='accepted')

        # create pickup_delivery
        pickup = PickupDelivery.objects.create(donation_request=req, donor=self.donor, ngo=self.ngo, medicine=self.med, status='pending', quantity_scheduled=1)
        self.assertEqual(pickup.status, 'pending')

        # legacy delivery flow removed; use new porter delivery request flow

        # simulate pickup -> in transit -> delivered via porter
        pickup.status = 'picked_up'
        pickup.pickup_date = timezone.now()
        pickup.quantity_picked_up = 1
        pickup.save()

        pickup.status = 'in_transit'
        pickup.save()

        pickup.status = 'delivered'
        pickup.delivery_date = timezone.now()
        pickup.quantity_delivered = 1
        pickup.save()

        # final assertions
        self.assertEqual(PickupDelivery.objects.get(pk=pickup.pk).status, 'delivered')
