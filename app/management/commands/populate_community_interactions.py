from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Medicine, DonationRequest, PickupDelivery, Conversation, Message, Notification, PorterPartner, DeliveryRequest, Testimonial
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create realistic interactions: donations, requests, acceptances, rejections, chats, and testimonials'

    def handle(self, *args, **options):
        # Get users
        donors = list(User.objects.filter(profile__role='donor'))
        ngos = list(User.objects.filter(profile__role='ngo'))
        individuals = list(User.objects.filter(profile__role='individual'))
        porter_services = list(PorterPartner.objects.all())
        
        if not donors or not ngos:
            self.stdout.write(self.style.ERROR('No donors or NGOs found. Please create users first.'))
            return
        
        # Get available medicines
        medicines = list(Medicine.objects.filter(status='available').exclude(name__icontains='expired')[:30])
        
        if not medicines:
            self.stdout.write(self.style.ERROR('No available medicines found.'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('Creating Realistic Community Interactions'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        # 1. Create various DONATION REQUESTS with different statuses
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Donation Requests...'))
        
        request_count = 0
        accepted_requests = []
        rejected_requests = []
        pending_requests = []
        
        for i in range(min(20, len(medicines))):
            medicine = random.choice(medicines)
            requester = random.choice(ngos)
            status = random.choices(['accepted', 'rejected', 'pending'], weights=[0.5, 0.2, 0.3])[0]
            
            quantity = max(5, min(medicine.quantity, 20))
            donation_request, created = DonationRequest.objects.get_or_create(
                medicine=medicine,
                requester=requester,
                defaults={
                    'requester_type': 'ngo',
                    'status': status,
                    'quantity_requested': random.randint(1, quantity),
                    'message': random.choice([
                        'We need this medicine urgently for our clinic',
                        'Please help us serve our patients better',
                        'Critical shortage at our facility',
                        'For our upcoming medical camp',
                        'Emergency supplies needed',
                        'Regular restocking for our hospital',
                        'High demand from patients',
                    ]),
                }
            )
            
            if created:
                request_count += 1
                if status == 'accepted':
                    accepted_requests.append(donation_request)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ ACCEPTED: {medicine.name} - {requester.username}'))
                elif status == 'rejected':
                    rejected_requests.append(donation_request)
                    self.stdout.write(self.style.WARNING(f'  ✗ REJECTED: {medicine.name} - {requester.username}'))
                else:
                    pending_requests.append(donation_request)
                    self.stdout.write(self.style.WARNING(f'  ⏳ PENDING: {medicine.name} - {requester.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {request_count} donation requests'))
        
        # 2. Create PICKUP/DELIVERY for accepted requests (mix of self-pickup and porter)
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Pickup/Delivery Records...'))
        
        pickup_count = 0
        
        for donation_request in accepted_requests:
            # 60% self-pickup, 40% porter service
            is_self_pickup = random.random() < 0.6
            
            pickup_delivery, created = PickupDelivery.objects.get_or_create(
                donation_request=donation_request,
                defaults={
                    'donor': donation_request.medicine.donor,
                    'ngo': donation_request.requester,
                    'medicine': donation_request.medicine,
                    'quantity_scheduled': donation_request.quantity_requested,
                    'status': random.choices(
                        ['pending', 'picked_up', 'in_transit', 'delivered'],
                        weights=[0.3, 0.2, 0.2, 0.3]
                    )[0],
                }
            )
            
            if created:
                pickup_count += 1
                
                # Update quantities based on status
                if pickup_delivery.status in ['picked_up', 'in_transit', 'delivered']:
                    pickup_delivery.quantity_picked_up = donation_request.quantity_requested
                    pickup_delivery.pickup_date = timezone.now() - timedelta(hours=random.randint(1, 24))
                
                if pickup_delivery.status in ['in_transit', 'delivered']:
                    pickup_delivery.quantity_delivered = donation_request.quantity_requested
                    pickup_delivery.delivery_date = timezone.now() - timedelta(hours=random.randint(1, 12))
                
                pickup_delivery.save()
                
                delivery_type = "SELF-PICKUP" if is_self_pickup else "PORTER"
                status_emoji = '✓' if pickup_delivery.status == 'delivered' else '→' if pickup_delivery.status == 'in_transit' else '○'
                self.stdout.write(f'  {status_emoji} {delivery_type}: {donation_request.medicine.name} - {pickup_delivery.get_status_display()}')
            
            # Create DeliveryRequest for porter services
            if not is_self_pickup and porter_services:
                porter = random.choice(porter_services)
                DeliveryRequest.objects.get_or_create(
                    pickup_delivery=pickup_delivery,
                    defaults={
                        'requester': donation_request.requester,
                        'porter_partner': porter,
                        'status': random.choice(['pending', 'sent', 'in_transit', 'delivered']),
                        'pickup_latitude': donation_request.medicine.latitude,
                        'pickup_longitude': donation_request.medicine.longitude,
                        'drop_latitude': donation_request.requester.profile.latitude,
                        'drop_longitude': donation_request.requester.profile.longitude,
                    }
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {pickup_count} pickup/delivery records'))
        
        # 3. Create CONVERSATIONS and MESSAGES between donors and NGOs
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Conversations & Messages...'))
        
        message_templates = {
            'greeting': [
                'Hi! Thanks for offering this medicine',
                'Hello, interested in getting this medicine',
                'Hi there! Do you have availability?',
                'Good day! Can we arrange pickup?',
            ],
            'logistics': [
                'Can we arrange a convenient pickup time?',
                'When would be the best time to collect?',
                'What\'s your preferred delivery method?',
                'Can we discuss the pickup logistics?',
                'Is self-pickup available from your location?',
            ],
            'confirmation': [
                'Great! We\'ll arrange the pickup',
                'Perfect! We\'re ready to receive it',
                'Thank you so much! This will help many people',
                'Excellent! We\'ll be there on time',
                'Confirmed! Thanks for your generosity',
            ],
            'gratitude': [
                'Thank you for donating! You\'re making a real difference',
                'We appreciate your help so much!',
                'This donation will help so many patients',
                'God bless you for your generosity',
                'Your donation came at the perfect time',
            ]
        }
        
        conversation_count = 0
        message_count = 0
        
        for donation_request in accepted_requests[:15]:  # Create conversations for 15 accepted requests
            conversation, created = Conversation.objects.get_or_create(
                donor=donation_request.medicine.donor,
                ngo=donation_request.requester,
                medicine=donation_request.medicine,
            )
            
            if created:
                conversation_count += 1
                
                # Create message thread
                messages_to_create = [
                    (donation_request.requester, random.choice(message_templates['greeting'])),
                    (donation_request.medicine.donor, random.choice(message_templates['logistics'])),
                    (donation_request.requester, random.choice(message_templates['confirmation'])),
                    (donation_request.medicine.donor, random.choice(message_templates['gratitude'])),
                ]
                
                for idx, (sender, content) in enumerate(messages_to_create):
                    message, msg_created = Message.objects.get_or_create(
                        conversation=conversation,
                        sender=sender,
                        content=content,
                        defaults={
                            'message_type': 'text',
                            'is_read': random.random() < 0.8,
                            'created_at': timezone.now() - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
                        }
                    )
                    if msg_created:
                        message_count += 1
            else:
                # Add occasional messages to existing conversations
                if random.random() < 0.3:
                    sender = random.choice([conversation.donor, conversation.ngo])
                    Message.objects.get_or_create(
                        conversation=conversation,
                        sender=sender,
                        content=random.choice(message_templates['logistics']),
                        defaults={
                            'message_type': 'text',
                            'is_read': random.random() < 0.7,
                        }
                    )
                    message_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {conversation_count} conversations'))
        self.stdout.write(self.style.SUCCESS(f'✓ Created {message_count} messages'))
        
        # 4. Create TESTIMONIALS from satisfied users
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Testimonials...'))
        
        testimonial_texts = [
            'MedShare helped us get medicines we desperately needed. Highly recommend!',
            'Amazing platform for connecting donors with those in need. Great experience!',
            'The donation process was so smooth. Thank you MedShare!',
            'We received high-quality medicines quickly. Truly grateful!',
            'This platform is changing lives. I\'ve donated several times now.',
            'As a donor, I felt good about contributing to society through MedShare.',
            'The NGO network here is incredible. Great coordination!',
            'MedShare made it easy to reach out for help when we needed it most.',
            'Best medical donation platform I\'ve used. Reliable and trustworthy.',
            'Supporting MedShare because it supports our community\'s health.',
            'Our patients have been helped so much thanks to this initiative.',
            'Simple, transparent, and truly making a difference. Love it!',
            'As a healthcare professional, I appreciate what MedShare does.',
            'This is the future of medicine donation. Proud to be part of it!',
            'MedShare: connecting hearts to help those in need.',
        ]
        
        testimonial_count = 0
        
        for i in range(12):
            user = random.choice(donors + ngos)
            role = user.profile.role
            
            testimonial, created = Testimonial.objects.get_or_create(
                user=user,
                name=f"{user.first_name} {user.last_name}",
                defaults={
                    'role': role,
                    'message': random.choice(testimonial_texts),
                    'approved': random.random() < 0.9,  # 90% approved
                }
            )
            
            if created:
                testimonial_count += 1
                self.stdout.write(f'  ✓ {testimonial.name} ({role}): "{testimonial.message[:50]}..."')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {testimonial_count} testimonials'))
        
        # 5. Create NOTIFICATIONS for interactions
        self.stdout.write(self.style.SUCCESS('\n▶ Creating Notifications...'))
        
        notification_count = 0
        
        for donation_request in accepted_requests[:10]:
            # NGO received notification
            notif1, created = Notification.objects.get_or_create(
                user=donation_request.requester,
                title='Donation Request Accepted',
                defaults={
                    'message': f'Your request for {donation_request.medicine.name} has been accepted by {donation_request.medicine.donor.first_name}',
                    'donation_request': donation_request,
                    'is_read': random.random() < 0.6,
                }
            )
            if created:
                notification_count += 1
            
            # Donor received notification
            notif2, created = Notification.objects.get_or_create(
                user=donation_request.medicine.donor,
                title='Medicine Request Received',
                defaults={
                    'message': f'{donation_request.requester.profile.organization_name} has accepted your donation of {donation_request.medicine.name}',
                    'donation_request': donation_request,
                    'is_read': random.random() < 0.6,
                }
            )
            if created:
                notification_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {notification_count} notifications'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✓ COMMUNITY INTERACTIONS COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS(f'  Donation Requests: {request_count}'))
        self.stdout.write(self.style.SUCCESS(f'    ├─ Accepted: {len(accepted_requests)}'))
        self.stdout.write(self.style.SUCCESS(f'    ├─ Rejected: {len(rejected_requests)}'))
        self.stdout.write(self.style.SUCCESS(f'    └─ Pending: {len(pending_requests)}'))
        self.stdout.write(self.style.SUCCESS(f'  Pickup/Delivery Records: {pickup_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Conversations: {conversation_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Messages: {message_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Testimonials: {testimonial_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Notifications: {notification_count}'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        self.stdout.write(self.style.SUCCESS('🎉 Your website now looks like a LIVE COMMUNITY with real interactions!'))
        self.stdout.write(self.style.SUCCESS('   - Donors have given medicines'))
        self.stdout.write(self.style.SUCCESS('   - NGOs have requested and received medicines'))
        self.stdout.write(self.style.SUCCESS('   - Some requests were rejected, some accepted'))
        self.stdout.write(self.style.SUCCESS('   - Real conversations between donors and NGOs'))
        self.stdout.write(self.style.SUCCESS('   - Mix of self-pickup and porter service delivery'))
        self.stdout.write(self.style.SUCCESS('   - People are thanking each other and sharing testimonials'))
        self.stdout.write(self.style.SUCCESS('   - System notifications tracking all interactions\n'))
