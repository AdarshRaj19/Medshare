from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta
from math import radians, cos, sin, asin, sqrt
import secrets
from io import BytesIO
import csv
from django.urls import reverse

from .models import (
    Medicine, DonationRequest, UserProfile, MedicineRating,
    MedicineSearchLog, Notification, ContactMessage, Testimonial, FAQ, PasswordResetToken,
    PickupDelivery,
    MedicineCategory, MedicineSubcategory, MedicineVerification, EmergencyAlert,
    AuditLog, BulkDonationRequest, BulkDonationItem, MedicineReport, MedicineInventory
)
from .forms import (
    MedicineForm, UserSignupForm, UserProfileForm, UserLoginForm,
    DonationRequestForm, MedicineRatingForm, MedicineSearchForm,
    ContactMessageForm, ForgotPasswordForm, ResetPasswordForm, TestimonialForm,
    EmergencyAlertForm, BulkDonationRequestForm, BulkDonationItemForm,
    MedicineVerificationForm, MedicineInventoryForm, AdvancedMedicineSearchForm
)
from .recommender import MedicineRecommender
from .decorators import role_required


# Utility: Auto-mark expired medicines globally
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

def auto_mark_expired_medicines():
    from .models import Medicine
    for med in Medicine.objects.filter(status__in=['available', 'requested']):
        med.mark_expired_if_needed()


def home(request):
    """Home page with statistics and featured medicines"""
    auto_mark_expired_medicines()
    total_medicines = Medicine.objects.filter(status='available').available_only().count()
    total_donors = User.objects.filter(profile__role='donor').count()
    total_ngos = User.objects.filter(profile__role='ngo').count()
    
    # Featured medicines (highly rated, non-expired)
    featured = Medicine.objects.filter(
        status='available'
    ).available_only().annotate(
        avg_rating=Avg('ratings__rating')
    ).order_by('-avg_rating')[:6]

    # AI recommendations (personalized when logged in)
    ai_recommendations = []
    ai_title = ""
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            recommender = MedicineRecommender(request.user)
            ai_recommendations = recommender.get_personalized_recommendations(limit=6)
            ai_title = (
                "Recommended for you"
                if request.user.profile.role == "ngo"
                else "High-demand medicines"
            )
        except Exception:
            ai_recommendations = []
            ai_title = ""
    
    # Unread notifications count
    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    
    context = {
        'total_medicines': total_medicines,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'featured_medicines': featured,
        'unread_notifications_count': unread_notifications_count,
        'ai_recommendations': ai_recommendations,
        'ai_title': ai_title,
    }
    return render(request, 'home.html', context)


def signup(request):
    """User registration for donors and NGOs"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create or update user profile
            role = request.POST.get('role', 'donor')
            profile = UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': role,
                    'phone': request.POST.get('phone'),
                    'organization_name': request.POST.get('organization_name'),
                }
            )[0]

            # legacy: delivery_boy role removed — no extra object created

            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
    else:
        form = UserSignupForm()

    return render(request, 'signup.html', {'form': form})


def user_login(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Prevent inactive users from logging in
                if not user.is_active:
                    form.add_error(None, 'Account is inactive. Contact support.')
                else:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")

                    if user.is_superuser:
                        return redirect('admin_reports')

                    # Redirect based on role
                    role = getattr(user.profile, 'role', None)
                    if role == 'donor':
                        return redirect('donor_dashboard')
                    elif role == 'ngo':
                        return redirect('ngo_dashboard')
                    else:
                        return redirect('home')

    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})

@login_required
@login_required
def user_profile(request):
    """
    User profile page with update form for phone, org, bio, lat/lon, and profile picture
    """
    from .forms import UserProfileForm
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'user_profile.html', {'form': form, 'user': request.user})


@login_required
@role_required('donor')
def donor_dashboard(request):
    try:
        if request.user.profile.role != 'donor':
            messages.error(request, "Only donors can access this dashboard.")
            return redirect('home')
    except Exception:
        messages.error(request, "Profile not found. Please contact admin.")
        return redirect('home')
    # Donor dashboard - list of donated medicines
    auto_mark_expired_medicines()
    medicines = Medicine.objects.filter(donor=request.user).annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    )

    # Add days until expiry
    for med in medicines:
        med.days_left = med.days_until_expiry()
        med.expiring_soon = med.is_expiring_soon()

    # Statistics
    total = medicines.count()
    available = medicines.filter(status='available').count()
    donated_agg = DonationRequest.objects.filter(
        medicine__donor=request.user,
        status='completed'
    ).aggregate(total_donated=Sum('quantity_requested'))
    donated = donated_agg.get('total_donated') or 0
    pending_requests = DonationRequest.objects.filter(medicine__donor=request.user, status='pending').count()
    accepted_requests = DonationRequest.objects.filter(medicine__donor=request.user, status='accepted').count()
    rejected_requests = DonationRequest.objects.filter(medicine__donor=request.user, status='rejected').count()
    context = {
        'medicines': medicines,
        'total': total,
        'available': available,
        'donated': donated,
        'pending_requests': pending_requests,
        'accepted_requests': accepted_requests,
        'rejected_requests': rejected_requests,
    }
    return render(request, 'donor_dashboard.html', context)


@login_required
@role_required('donor')
@login_required
@role_required('donor')
def edit_medicine(request, med_id):
    """Edit an existing medicine donation (donor-only, owner-only)."""
    # Prevent IDOR: only allow editing own medicines
    try:
        medicine = Medicine.objects.get(id=med_id, donor=request.user)
    except Medicine.DoesNotExist:
        return redirect('donor_dashboard')

    if request.method == "POST":
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated.")
            return redirect("donor_dashboard")
    else:
        form = MedicineForm(instance=medicine)

    return render(request, "edit_medicine.html", {"form": form, "medicine": medicine})


@login_required
@role_required('donor')
@require_POST
def delete_medicine(request, med_id):
    """Delete a medicine donation (donor-only, owner-only)."""
    medicine = get_object_or_404(Medicine, id=med_id, donor=request.user)
    medicine.delete()
    messages.success(request, "Medicine deleted.")
    return redirect("donor_dashboard")


@login_required
@role_required('donor')
@csrf_exempt
def add_medicine(request):
    """Add new medicine donation with duplicate detection"""
    try:
        profile = request.user.profile
        if profile.role != 'donor':
            messages.error(request, "Only donors can add medicines.")
            return redirect('home')
    except:
        messages.error(request, "Profile not found. Please contact admin.")
        return redirect('home')
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                med = form.save(commit=False)
                med.donor = request.user
                # Prevent adding expired medicines
                if med.is_expired():
                    messages.error(request, "Cannot add a medicine that is already expired.")
                    return render(request, 'add_medicine.html', {'form': form})
                # Check for duplicates (same name + expiry date)
                duplicates = med.find_duplicates()
                if duplicates.exists():
                    # Auto-merge with first duplicate
                    duplicate_med = duplicates.first()
                    med.id = duplicate_med.id  # Reuse same ID
                    med.quantity += duplicate_med.quantity
                    med.save()
                    messages.success(request, f"Medicine merged! Quantity increased by {duplicate_med.quantity} units.")
                else:
                    med.save()
                    messages.success(request, "Medicine listed for donation.")
                return redirect('donor_dashboard')
            except Exception as e:
                messages.error(request, f"Error saving medicine: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MedicineForm()

    return render(request, 'add_medicine.html', {'form': form})


@login_required
@role_required('donor','ngo','admin','individual')
def medicine_detail(request, med_id):
    """View medicine details"""
    medicine = get_object_or_404(Medicine, id=med_id)
    
    # Log view
    medicine.viewed_by.add(request.user)
    
    # Get ratings
    ratings = medicine.ratings.all()
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()

    context = {
        'medicine': medicine,
        'ratings': ratings,
        'avg_rating': avg_rating,
        'user_rating': user_rating,
        'days_left': medicine.days_until_expiry(),
    }
    return render(request, 'medicine_detail.html', context)


@role_required('donor','ngo','admin','individual')
def rate_medicine(request, med_id):
    medicine = get_object_or_404(Medicine, id=med_id)

    if request.method == "POST":
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            med = form.save(commit=False)

            # Prevent expired medicine
            if med.is_expired():
                messages.error(
                    request,
                    "Cannot set expiry date in the past or edit to expired medicine."
                )
                return render(
                    request,
                    "rate_medicine.html",
                    {"form": form, "medicine": medicine}
                )

            med.save()
            messages.success(request, "Medicine updated successfully.")
            return redirect("donor_dashboard")

    else:
        form = MedicineForm(instance=medicine)

    # ✅ THIS LINE WAS MISSING
    return render(
        request,
        "rate_medicine.html",
        {"form": form, "medicine": medicine}
    )

# The following code block was incorrectly indented and is likely from the rate_medicine view, not edit_medicine.
# If this is part of rate_medicine, it should be in its own function, not here.


@login_required
@role_required('ngo', 'individual')
def ngo_dashboard(request):
    try:
        if request.user.profile.role not in ['ngo', 'individual']:
            messages.error(request, "Only NGOs and individuals can access this dashboard.")
            return redirect('home')
    except Exception:
        messages.error(request, "Profile not found. Please contact admin.")
        return redirect('home')
    """NGO/Individual dashboard - search and request medicines"""
    auto_mark_expired_medicines()
    # Enforce role to prevent URL bypass
    if request.user.profile.role not in ['ngo', 'individual']:
        return redirect('home')
    
    form = MedicineSearchForm(request.GET)
    medicines = Medicine.objects.filter(status='available').available_only().annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    )
    if form.is_valid():
        query = form.cleaned_data.get('query')
        expiring_soon = form.cleaned_data.get('expiring_soon')
        rating_min = form.cleaned_data.get('rating_min')
        if query:
            medicines = medicines.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        if expiring_soon:
            cutoff_date = date.today() + timedelta(days=30)
            medicines = medicines.filter(expiry_date__lte=cutoff_date)
        if rating_min:
            medicines = medicines.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=rating_min)
        # Log search (AI training/analytics)
        if query:
            try:
                MedicineRecommender(request.user).log_search(query, list(medicines[:10]))
            except Exception:
                pass
    # Statistics
    requests_pending = DonationRequest.objects.filter(requester=request.user, status='pending').count()
    requests_accepted = DonationRequest.objects.filter(requester=request.user, status='accepted').count()
    requests_rejected = DonationRequest.objects.filter(requester=request.user, status='rejected').count()
    received_count = DonationRequest.objects.filter(requester=request.user, status='completed').count()
    context = {
        'medicines': medicines,
        'form': form,
        'requests_pending': requests_pending,
        'requests_accepted': requests_accepted,
        'requests_rejected': requests_rejected,
        'received_count': received_count,
    }
    # AI recommendations
    try:
        context["ai_recommendations"] = MedicineRecommender(request.user).get_ngo_recommendations(limit=6)
    except Exception:
        context["ai_recommendations"] = []
    return render(request, 'ngo_dashboard.html', context)


@login_required
@role_required('ngo', 'individual')
def request_medicine(request, med_id):
    """Request a medicine (for NGOs and individuals)"""
    # Ensure only available medicines can be requested
    try:
        medicine = Medicine.objects.get(id=med_id, status='available')
        # Prevent requesting expired medicines
        if medicine.is_expired():
            messages.error(request, "Cannot request an expired medicine.")
            return redirect('ngo_dashboard')
    except Medicine.DoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation_req = form.save(commit=False)
            donation_req.medicine = medicine
            donation_req.requester = request.user
            donation_req.requester_type = 'ngo' if request.user.profile.role == 'ngo' else 'individual'
            donation_req.save()

            # Create notification for donor
            Notification.objects.create(
                user=medicine.donor,
                title='Medicine Request',
                message=f"{request.user.first_name or request.user.username} requested {medicine.name}",
                donation_request=donation_req
            )
            # Notify requester (NGO/individual)
            Notification.objects.create(
                user=request.user,
                title='Request Submitted',
                message=f"Your request for {medicine.name} has been submitted to the donor.",
                donation_request=donation_req
            )

            return redirect('donation_request_detail', req_id=donation_req.id)
    else:
        form = DonationRequestForm()

    context = {
        'medicine': medicine,
        'form': form,
    }
    return render(request, 'request_medicine.html', context)


@login_required
@role_required('donor', 'ngo', 'admin', 'individual')
def donation_request_detail(request, req_id):
    """View donation request details and allow NGO to choose delivery method"""

    donation_req = get_object_or_404(DonationRequest, id=req_id)

    # Check permissions
    if request.user != donation_req.requester and request.user != donation_req.medicine.donor:
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        # ACCEPT
        if action == 'accept' and request.user == donation_req.medicine.donor:
            if donation_req.status != 'pending':
                messages.error(request, "Only pending requests can be accepted.")
            else:
                with transaction.atomic():
                    donation_req.status = 'accepted'
                    donation_req.save()
                    Notification.objects.create(
                        user=donation_req.requester,
                        title='Request Accepted',
                        message=f"Your request for {donation_req.medicine.name} has been accepted. Choose your delivery method.",
                        donation_request=donation_req
                    )
                    # Create PickupDelivery record but don't auto-create DeliveryRequest
                    # NGO will choose delivery method after acceptance
                    from app.models import PickupDelivery
                    if not hasattr(donation_req, 'pickup_delivery'):
                        qty = donation_req.quantity_requested or donation_req.medicine.quantity or 1
                        PickupDelivery.objects.create(
                            medicine=donation_req.medicine,
                            donation_request=donation_req,
                            ngo=donation_req.requester,
                            donor=donation_req.medicine.donor,
                            status='pending',
                            quantity_scheduled=qty,
                        )
                    messages.success(request, "Request accepted! NGO will now choose delivery method.")
        
        # NGO CHOOSES DELIVERY METHOD
        elif action == 'choose_delivery' and request.user == donation_req.requester:
            if donation_req.status != 'accepted':
                messages.error(request, "Request must be accepted first.")
            else:
                delivery_method = request.POST.get('delivery_method')  # 'self_pickup' or 'porter'
                
                if not hasattr(donation_req, 'pickup_delivery'):
                    messages.error(request, "Pickup/Delivery record not found.")
                    return redirect('donation_request_detail', req_id=req_id)
                
                pickup_delivery = donation_req.pickup_delivery
                
                if delivery_method == 'self_pickup':
                    # NGO will self-pickup - no porter service needed
                    Notification.objects.create(
                        user=donation_req.medicine.donor,
                        title='Self Pickup Selected',
                        message=f"NGO will self-pickup {donation_req.medicine.name}. Coordinate pickup timing.",
                        donation_request=donation_req
                    )
                    messages.success(request, "Self-pickup selected. Coordinate with donor for pickup timing.")
                
                elif delivery_method == 'porter':
                    # Create DeliveryRequest for external porter partners
                    from app.models import DeliveryRequest
                    
                    if not hasattr(pickup_delivery, 'delivery_request'):
                        ngo_profile = donation_req.requester.profile
                        donor_profile = donation_req.medicine.donor.profile
                        
                        pickup_lat = donor_profile.latitude if donor_profile and donor_profile.latitude else donation_req.medicine.latitude
                        pickup_lng = donor_profile.longitude if donor_profile and donor_profile.longitude else donation_req.medicine.longitude
                        drop_lat = ngo_profile.latitude if ngo_profile and ngo_profile.latitude else None
                        drop_lng = ngo_profile.longitude if ngo_profile and ngo_profile.longitude else None
                        
                        delivery_request = DeliveryRequest.objects.create(
                            pickup_delivery=pickup_delivery,
                            requester=donation_req.requester,
                            pickup_latitude=pickup_lat,
                            pickup_longitude=pickup_lng,
                            drop_latitude=drop_lat,
                            drop_longitude=drop_lng,
                            status='pending'
                        )
                        
                        Notification.objects.create(
                            user=donation_req.requester,
                            title='Porter Service Requested',
                            message=f"Porter service requested for {donation_req.medicine.name}. Platform will coordinate with partners.",
                            donation_request=donation_req
                        )
                        for admin in User.objects.filter(is_superuser=True):
                            Notification.objects.create(
                                user=admin,
                                title='Delivery Request Created',
                                message=f"DeliveryRequest #{delivery_request.id} for {donation_req.medicine.name}. Coordinate with porter partners.",
                                donation_request=donation_req
                            )
                        messages.success(request, "Porter service requested. Platform will coordinate with delivery partners.")
        
        # REJECT
        elif action == 'reject' and request.user == donation_req.medicine.donor:
            if donation_req.status != 'pending':
                messages.error(request, "Only pending requests can be rejected.")
            else:
                donation_req.status = 'rejected'
                donation_req.save()
                Notification.objects.create(
                    user=donation_req.requester,
                    title='Request Rejected',
                    message=f"Your request for {donation_req.medicine.name} has been rejected",
                    donation_request=donation_req
                )
                for admin in User.objects.filter(is_superuser=True):
                    Notification.objects.create(
                        user=admin,
                        title='Request Rejected',
                        message=f"Request for {donation_req.medicine.name} by {donation_req.requester.username} was rejected by donor.",
                        donation_request=donation_req
                    )
        # COMPLETE
        elif action == 'complete' and request.user == donation_req.medicine.donor:
            if donation_req.status != 'accepted':
                messages.error(request, "Only accepted requests can be completed.")
            else:
                with transaction.atomic():
                    donation_req.status = 'completed'
                    donation_req.completed_at = date.today()
                    med = donation_req.medicine
                    qty_requested = donation_req.quantity_requested or 0
                    if qty_requested and med.quantity:
                        med.quantity = max(0, med.quantity - qty_requested)
                    med.status = 'donated' if med.quantity == 0 else 'available'
                    med.save(update_fields=['quantity', 'status', 'updated_at'])
                    donation_req.save()
                Notification.objects.create(
                    user=donation_req.requester,
                    title='Request Completed',
                    message=f"Your request for {donation_req.medicine.name} has been completed",
                    donation_request=donation_req
                )
        else:
            messages.error(request, "Invalid action or insufficient permissions.")

    # After acceptance, delivery is handled by external porter partners
    can_update_logistics = False
    context = {
        'donation_request': donation_req,
        'medicine': donation_req.medicine,
        'can_update_logistics': can_update_logistics,
    }
    return render(request, 'donation_request_detail.html', context)


@login_required
@role_required('donor','ngo','admin','individual')
def notifications(request):
    """View user notifications"""
    notifs = request.user.notifications.all()

    if request.method == 'POST':
        notif_id = request.POST.get('notif_id')
        action = request.POST.get('action')

        if action == 'mark_read':
            notif = get_object_or_404(Notification, id=notif_id, user=request.user)
            notif.is_read = True
            notif.save()

    context = {
        'notifications': notifs,
        'unread_count': notifs.filter(is_read=False).count(),
    }
    return render(request, 'notifications.html', context)


def is_admin(user):
    """Check if user is admin"""
    return user.is_superuser


@login_required
@role_required('admin')
def admin_reports(request):
    try:
        if not request.user.is_superuser and request.user.profile.role != 'admin':
            messages.error(request, "Only admins can access this dashboard.")
            return redirect('home')
    except Exception:
        messages.error(request, "Profile not found. Please contact admin.")
        return redirect('home')
    """Admin dashboard with reports"""
    total_medicines = Medicine.objects.count()
    available = Medicine.objects.filter(status='available').count()
    donated = Medicine.objects.filter(status='donated').count()
    expired = Medicine.objects.filter(status='expired').count()

    total_donors = User.objects.filter(profile__role='donor').count()
    total_ngos = User.objects.filter(profile__role='ngo').count()

    total_requests = DonationRequest.objects.count()
    pending_requests = DonationRequest.objects.filter(status='pending').count()

    # Top medicines
    top_medicines = Medicine.objects.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).order_by('-avg_rating')[:5]

    context = {
        'total_medicines': total_medicines,
        'available': available,
        'donated': donated,
        'expired': expired,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'top_medicines': top_medicines,
    }
    return render(request, 'admin_reports.html', context)


@login_required
@role_required('admin')
def admin_delivery_requests(request):
    """Admin view to list DeliveryRequests and assign Porter partners / tracking links."""
    from .models import DeliveryRequest, PorterPartner

    if request.method == 'POST':
        dr_id = request.POST.get('dr_id')
        partner_id = request.POST.get('partner_id')
        link = request.POST.get('external_tracking_link')
        status = request.POST.get('status')

        dr = get_object_or_404(DeliveryRequest, id=dr_id)
        if partner_id:
            try:
                dr.porter_partner = PorterPartner.objects.get(id=int(partner_id))
            except Exception:
                dr.porter_partner = None
        if link is not None:
            dr.external_tracking_link = link or None
        if status in dict(DeliveryRequest.STATUS_CHOICES):
            dr.status = status
        dr.save()

        # Notify requester
        try:
            Notification.objects.create(
                user=dr.requester,
                title='Delivery Partner Assigned',
                message=f'Partner assigned for your delivery request #{dr.id}. Tracking link will be shared when available.',
                donation_request=dr.pickup_delivery.donation_request
            )
        except Exception:
            pass

        messages.success(request, 'DeliveryRequest updated.')
        return redirect('admin_delivery_requests')

    partners = PorterPartner.objects.filter(active=True)
    delivery_requests = DeliveryRequest.objects.select_related('pickup_delivery__medicine', 'requester', 'porter_partner').order_by('-created_at')

    context = {
        'delivery_requests': delivery_requests,
        'partners': partners,
    }
    return render(request, 'admin_delivery_requests.html', context)


@login_required
@role_required('donor','ngo','admin','individual')
def medicines_map(request):
    """View medicines on map"""
    medicines = Medicine.objects.filter(
        status='available',
        latitude__isnull=False,
        longitude__isnull=False
    ).annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    )

    medicine_markers = list(
        medicines.values(
            "id",
            "name",
            "quantity",
            "unit",
            "expiry_date",
            "latitude",
            "longitude",
            "location_name",
        )
    )

    context = {
        'medicines': medicines,
        'medicine_markers': medicine_markers,
    }
    return render(request, 'medicines_map.html', context)


@login_required
@role_required('donor','ngo','admin','individual')
def search_medicines(request):
    """Advanced medicine search with filters"""
    form = MedicineSearchForm(request.GET)
    medicines = Medicine.objects.filter(status='available').annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    )

    if form.is_valid():
        query = form.cleaned_data.get('query')
        expiring_soon = form.cleaned_data.get('expiring_soon')
        rating_min = form.cleaned_data.get('rating_min')

        if query:
            medicines = medicines.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if expiring_soon:
            cutoff_date = date.today() + timedelta(days=30)
            medicines = medicines.filter(expiry_date__lte=cutoff_date)

        if rating_min:
            medicines = medicines.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=rating_min)

        # Log search (AI training/analytics)
        if query:
            try:
                MedicineRecommender(request.user).log_search(query, list(medicines[:10]))
            except Exception:
                pass

    context = {
        'medicines': medicines,
        'form': form,
    }
    return render(request, 'search_medicines.html', context)


# ============= NEW MISSING FEATURES =============

def about(request):
    """About page with mission, vision, and statistics"""
    total_medicines_donated = Medicine.objects.filter(status='donated').count()
    total_ngos = User.objects.filter(profile__role='ngo').count()
    total_donors = User.objects.filter(profile__role='donor').count()
    total_lives_helped = DonationRequest.objects.filter(status='completed').count()

    context = {
        'total_medicines_donated': total_medicines_donated,
        'total_ngos': total_ngos,
        'total_donors': total_donors,
        'total_lives_helped': total_lives_helped,
    }
    return render(request, 'about.html', context)


def contact(request):
    """Contact page with contact form and auto-reply"""
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_msg = form.save()
            
            # Send auto-reply email
            try:
                send_mail(
                    subject='We received your message',
                    message=f'''Thank you for contacting MedShare!

We have received your message: "{form.cleaned_data['subject']}"

Our team will review your message and get back to you soon.

Best regards,
MedShare Team''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[contact_msg.email],
                    fail_silently=True,
                )
            except:
                pass

            messages.success(request, "Thank you! Your message has been sent. We'll get back to you soon.")
            return redirect('home')
    else:
        form = ContactMessageForm()

    context = {'form': form}
    return render(request, 'contact.html', context)


def faq(request):
    """FAQ/Help page with categorized questions"""
    faqs = FAQ.objects.filter(active=True).order_by('order')
    categories = dict(FAQ._meta.get_field('category').choices)

    # Group FAQs by category
    faqs_by_category = {}
    for faq in faqs:
        if faq.category not in faqs_by_category:
            faqs_by_category[faq.category] = []
        faqs_by_category[faq.category].append(faq)

    context = {
        'faqs': faqs,
        'faqs_by_category': faqs_by_category,
        'categories': categories,
    }
    return render(request, 'faq.html', context)


def forgot_password(request):
    """Forgot password form"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Create reset token
                token = secrets.token_urlsafe(32)
                expires_at = timezone.now() + timedelta(hours=24)
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )

                # Send reset email
                reset_link = f"{request.build_absolute_uri('/reset-password/')}{token}/"
                send_mail(
                    subject='MedShare Password Reset',
                    message=f'''Click the link below to reset your password:

{reset_link}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
MedShare Team''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "Password reset link sent to your email!")
            except User.DoesNotExist:
                messages.error(request, "Email not found in our records.")
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})


def reset_password(request, token):
    """Reset password with token"""
    if request.user.is_authenticated:
        return redirect('home')

    try:
        reset_token = PasswordResetToken.objects.get(token=token, used=False)
        
        # Check if token expired
        if reset_token.expires_at < timezone.now():
            messages.error(request, "This password reset link has expired.")
            return redirect('forgot_password')

        if request.method == 'POST':
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                reset_token.user.set_password(form.cleaned_data['password'])
                reset_token.user.save()
                reset_token.used = True
                reset_token.save()

                messages.success(request, "Password reset successful! Please login with your new password.")
                return redirect('login')
        else:
            form = ResetPasswordForm()

        return render(request, 'reset_password.html', {'form': form, 'token': token})

    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid password reset link.")
        return redirect('forgot_password')


@login_required
@role_required('donor','ngo','admin','individual')
def expiry_tracker(request):
    """Real-time expiry tracker showing all medicines with countdown"""
    auto_mark_expired_medicines()
    if request.user.profile.role == 'donor':
        medicines = Medicine.objects.filter(donor=request.user, status='available')
    elif request.user.profile.role == 'individual':
        # Individuals see all available medicines for expiry tracking
        medicines = Medicine.objects.filter(status='available')
    else:
        # NGO/delivery only sees non-expired medicines
        medicines = Medicine.objects.filter(status='available').available_only()

    # Categorize medicines by expiry status
    expiring_soon = []
    expiring_very_soon = []
    already_expired = []
    normal = []

    for medicine in medicines:
        days_left = medicine.days_until_expiry()
        medicine.days_left = days_left

        if days_left < 0:
            already_expired.append(medicine)
        elif days_left <= 7:
            expiring_very_soon.append(medicine)
        elif days_left <= 30:
            expiring_soon.append(medicine)
        else:
            normal.append(medicine)

    context = {
        'expiring_very_soon': expiring_very_soon,
        'expiring_soon': expiring_soon,
        'already_expired': already_expired,
        'normal': normal,
        'total_medicines': len(medicines),
    }
    return render(request, 'expiry_tracker.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_reports_advanced(request):
    """Advanced admin reports with charts and export options"""
    # Get all data
    total_medicines = Medicine.objects.count()
    available = Medicine.objects.filter(status='available').count()
    donated = Medicine.objects.filter(status='donated').count()
    expired = Medicine.objects.filter(status='expired').count()

    total_donors = User.objects.filter(profile__role='donor').count()
    total_ngos = User.objects.filter(profile__role='ngo').count()

    total_requests = DonationRequest.objects.count()
    pending_requests = DonationRequest.objects.filter(status='pending').count()
    completed_requests = DonationRequest.objects.filter(status='completed').count()

    # Top medicines
    top_medicines = Medicine.objects.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).order_by('-avg_rating')[:5]

    # Donations per month (last 12 months)
    from django.db.models.functions import TruncDate
    donations_per_month = DonationRequest.objects.filter(
        status='completed'
    ).extra(
        select={'month': 'strftime("%Y-%m", created_at)'}
    ).values('month').annotate(count=Count('id')).order_by('month')

    context = {
        'total_medicines': total_medicines,
        'available': available,
        'donated': donated,
        'expired': expired,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'top_medicines': top_medicines,
        'donations_per_month': list(donations_per_month),
    }
    return render(request, 'admin_reports_advanced.html', context)


@user_passes_test(lambda u: u.is_superuser)
def export_reports_csv(request):
    """Export admin reports as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medshare_reports.csv"'

    writer = csv.writer(response)
    
    # Write summary statistics
    writer.writerow(['MedShare Report', f'Generated on {date.today()}'])
    writer.writerow([])
    
    writer.writerow(['SUMMARY STATISTICS'])
    writer.writerow(['Total Medicines', Medicine.objects.count()])
    writer.writerow(['Available Medicines', Medicine.objects.filter(status='available').count()])
    writer.writerow(['Donated Medicines', Medicine.objects.filter(status='donated').count()])
    writer.writerow(['Expired Medicines', Medicine.objects.filter(status='expired').count()])
    writer.writerow(['Total Donors', User.objects.filter(profile__role='donor').count()])
    writer.writerow(['Total NGOs', User.objects.filter(profile__role='ngo').count()])
    writer.writerow([])
    
    # Write donation requests
    writer.writerow(['DONATION REQUESTS'])
    writer.writerow(['Medicine Name', 'Donor', 'Requester', 'Type', 'Status', 'Date'])
    for req in DonationRequest.objects.select_related('medicine', 'medicine__donor', 'requester'):
        writer.writerow([
            req.medicine.name,
            req.medicine.donor.username,
            req.requester.username,
            req.requester_type,
            req.status,
            req.created_at.strftime('%Y-%m-%d')
        ])

    return response


def add_testimonial(request):
    """Add testimonial form"""
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            testimonial = form.save(commit=False)
            if request.user.is_authenticated:
                testimonial.user = request.user
            testimonial.save()
            messages.success(request, "Thank you! Your testimonial will be reviewed and published soon.")
            return redirect('home')
    else:
        form = TestimonialForm()

    return render(request, 'add_testimonial.html', {'form': form})


def testimonials(request):
    """View approved testimonials"""
    testimonials_list = Testimonial.objects.filter(approved=True).order_by('-created_at')
    context = {'testimonials': testimonials_list}
    return render(request, 'testimonials.html', context)

@login_required
@role_required('donor','ngo','admin')


@login_required
@role_required('ngo')




# ============================================
# DELIVERY BOY & LIVE TRACKING SYSTEM
# ============================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    r = 6371  # Radius of earth in kilometers
    return c * r

 
# ============= EMERGENCY ALERTS =============

@login_required
@role_required('donor','ngo','delivery_boy','admin')
def emergency_alerts(request):
    """View all active emergency alerts"""
    # Enforce NGO-only view (donors can see but NGO priority)
    if request.user.profile.role not in ['ngo', 'admin', 'donor']:
        return redirect('home')
    
    alerts = EmergencyAlert.objects.filter(is_active=True).order_by('-priority', '-created_at')
    
    # Add time remaining for each alert
    for alert in alerts:
        if alert.deadline:
            alert.time_remaining = alert.deadline - timezone.now()
            alert.is_expired = alert.time_remaining.total_seconds() < 0
            if not alert.is_expired:
                alert.hours_remaining = int(alert.time_remaining.seconds // 3600)
            else:
                alert.hours_remaining = 0
        else:
            alert.time_remaining = None
            alert.is_expired = False
            alert.hours_remaining = None

    # For donor: get responses made
    donor_responses = {}
    if request.user.profile.role == 'donor':
        from .models import EmergencyAlertResponse
        donor_responses = {r.alert_id: r for r in EmergencyAlertResponse.objects.filter(donor=request.user)}

    context = {
        'alerts': alerts,
        'total_alerts': alerts.count(),
        'critical_alerts': alerts.filter(priority='critical').count(),
        'donor_responses': donor_responses,
    }
    return render(request, 'emergency_alerts.html', context)
# Donor: respond to emergency alert
@login_required
@role_required('donor')
def respond_emergency_alert(request, alert_id):
    alert = get_object_or_404(EmergencyAlert, id=alert_id, is_active=True)
    from .models import EmergencyAlertResponse
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity_offered', 1))
        message = request.POST.get('message', '')
        response, created = EmergencyAlertResponse.objects.get_or_create(
            alert=alert, donor=request.user,
            defaults={'quantity_offered': quantity, 'message': message}
        )
        if not created:
            # If donor updates their response, adjust the alert quantity accordingly
            alert.quantity_needed += response.quantity_offered  # revert previous offer
            response.quantity_offered = quantity
            response.message = message
            response.save()
        # Subtract the offered quantity from the alert
        alert.quantity_needed -= quantity
        if alert.quantity_needed <= 0:
            alert.is_active = False
            alert.resolved_at = timezone.now()
            alert.quantity_needed = 0
        alert.save()
        # Notify NGO about the donor response
        Notification.objects.create(
            user=alert.ngo,
            title='Donor Response to Emergency Alert',
            message=f"{request.user.username} offered {quantity} {alert.unit} for your alert: {alert.medicine_name}."
        )
        messages.success(request, "Your response has been submitted!")
        return redirect('emergency_alerts')
    return redirect('emergency_alerts')
# NGO/Admin: accept a donor response
@login_required
@role_required('ngo','admin')
def accept_emergency_response(request, response_id):
    from .models import EmergencyAlertResponse
    response = get_object_or_404(EmergencyAlertResponse, id=response_id)
    if request.user.profile.role == 'ngo' and response.alert.ngo != request.user:
        return redirect('emergency_alerts')
    response.accepted = True
    response.alert.is_active = False
    response.alert.resolved_at = timezone.now()
    response.alert.save()
    response.save()
    messages.success(request, "Donor response accepted and alert marked as resolved.")
    return redirect('emergency_alerts')


@login_required
@role_required('ngo')
def create_emergency_alert(request):
    """Create emergency alert (NGO only)"""
    if request.user.profile.role != 'ngo':
        messages.error(request, "Only NGOs can create emergency alerts.")
        return redirect('home')

    if request.method == 'POST':
        category_id = request.POST.get('medicine_category')
        medicine_name = request.POST.get('medicine_name')
        quantity_needed = request.POST.get('quantity_needed')
        unit = request.POST.get('unit', 'units')
        priority = request.POST.get('priority', 'medium')
        description = request.POST.get('description')
        patient_count = request.POST.get('patient_count')
        deadline = request.POST.get('deadline')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        location_name = request.POST.get('location_name')

        try:
            category = MedicineCategory.objects.get(id=category_id)
            alert = EmergencyAlert.objects.create(
                ngo=request.user,
                medicine_category=category,
                medicine_name=medicine_name,
                quantity_needed=int(quantity_needed),
                unit=unit,
                priority=priority,
                description=description,
                patient_count=int(patient_count) if patient_count else None,
                deadline=deadline if deadline else None,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                location_name=location_name or request.user.profile.organization_name,
            )
            
            # Notify ALL donors about the new emergency alert
            all_helpers = User.objects.filter(profile__role__in=['donor', 'individual'], is_active=True)
            for helper in all_helpers:
                Notification.objects.create(
                    user=helper,
                    title='Emergency Medicine Alert',
                    message=f'Urgent need for {medicine_name} at {request.user.profile.organization_name}. Priority: {priority.upper()}. Needed: {quantity_needed} {unit}.'
                )
            
            messages.success(request, "Emergency alert created successfully!")
            return redirect('emergency_alerts')
            
        except Exception as e:
            messages.error(request, f"Error creating alert: {str(e)}")
    
    categories = MedicineCategory.objects.filter(active=True)
    context = {'categories': categories}
    return render(request, 'create_emergency_alert.html', context)


@login_required
@role_required('ngo')
def resolve_emergency_alert(request, alert_id):
    """Resolve emergency alert (NGO only)"""
    alert = get_object_or_404(EmergencyAlert, id=alert_id, ngo=request.user)
    
    if request.method == 'POST':
        alert.is_active = False
        alert.resolved_at = timezone.now()
        alert.save()
        messages.success(request, "Emergency alert resolved.")
        return redirect('emergency_alerts')
    
    return redirect('emergency_alerts')


# ============= BULK DONATION REQUESTS =============

@login_required
@role_required('ngo')
def bulk_requests(request):
    """View bulk donation requests (NGO dashboard)"""
    if request.user.profile.role != 'ngo':
        return redirect('home')
    
    requests = BulkDonationRequest.objects.filter(ngo=request.user).order_by('-created_at')
    
    context = {
        'bulk_requests': requests,
        'draft_count': requests.filter(status='draft').count(),
        'submitted_count': requests.filter(status='submitted').count(),
        'completed_count': requests.filter(status='completed').count(),
    }
    return render(request, 'bulk_requests.html', context)


@login_required
@role_required('ngo')
def create_bulk_request(request):
    """Create bulk donation request (NGO only)"""
    if request.user.profile.role != 'ngo':
        messages.error(request, "Only NGOs can create bulk requests.")
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        
        bulk_request = BulkDonationRequest.objects.create(
            ngo=request.user,
            title=title,
            description=description,
            priority=priority,
            status='draft'
        )
        
        messages.success(request, "Bulk request created! Add items to it.")
        return redirect('edit_bulk_request', request_id=bulk_request.id)
    
    return render(request, 'create_bulk_request.html')


@login_required
@role_required('ngo')
def edit_bulk_request(request, request_id):
    """Edit bulk donation request"""
    bulk_request = get_object_or_404(BulkDonationRequest, id=request_id, ngo=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_item':
            category_id = request.POST.get('medicine_category')
            medicine_name = request.POST.get('medicine_name')
            quantity = request.POST.get('quantity_requested')
            unit = request.POST.get('unit', 'units')
            urgency = request.POST.get('urgency_level', 'medium')
            notes = request.POST.get('notes')
            
            try:
                category = MedicineCategory.objects.get(id=category_id)
                BulkDonationItem.objects.create(
                    bulk_request=bulk_request,
                    medicine_category=category,
                    medicine_name=medicine_name,
                    quantity_requested=int(quantity),
                    unit=unit,
                    urgency_level=urgency,
                    notes=notes,
                )
                messages.success(request, "Item added to bulk request.")
            except Exception as e:
                messages.error(request, f"Error adding item: {str(e)}")
                
        elif action == 'submit':
            if bulk_request.items.count() > 0:
                bulk_request.status = 'submitted'
                bulk_request.submitted_at = timezone.now()
                bulk_request.save()
                messages.success(request, "Bulk request submitted successfully!")
                return redirect('bulk_requests')
            else:
                messages.error(request, "Add at least one item before submitting.")
                
        elif action == 'delete_item':
            item_id = request.POST.get('item_id')
            try:
                item = BulkDonationItem.objects.get(id=item_id, bulk_request=bulk_request)
                item.delete()
                messages.success(request, "Item removed.")
            except BulkDonationItem.DoesNotExist:
                messages.error(request, "Item not found.")
    
    categories = MedicineCategory.objects.filter(active=True)
    context = {
        'bulk_request': bulk_request,
        'categories': categories,
    }
    return render(request, 'edit_bulk_request.html', context)


@login_required
@role_required('ngo')
def bulk_request_matches(request, request_id):
    """Find matching medicines for bulk request items"""
    bulk_request = get_object_or_404(BulkDonationRequest, id=request_id)
    
    # Check permissions
    if request.user != bulk_request.ngo and not request.user.is_superuser:
        return redirect('home')
    
    matches = {}
    for item in bulk_request.items.filter(status__in=['pending', 'partial']):
        # Find medicines that match this item
        matching_medicines = Medicine.objects.filter(
            status='available',
            category=item.medicine_category,
            name__icontains=item.medicine_name.split()[0]  # Match first word
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            ratings_count=Count('ratings')
        )[:5]  # Limit to 5 matches per item
        
        matches[item.id] = matching_medicines
    
    context = {
        'bulk_request': bulk_request,
        'matches': matches,
    }
    return render(request, 'bulk_request_matches.html', context)


# ============= MEDICINE CATEGORIES =============

def medicine_categories(request):
    """Browse medicines by category"""
    categories = MedicineCategory.objects.filter(active=True).prefetch_related('medicines')
    
    # Add medicine count for each category
    for category in categories:
        category.medicine_count = category.medicines.filter(status='available').count()
    
    context = {
        'categories': categories,
    }
    return render(request, 'medicine_categories.html', context)


def category_medicines(request, category_id):
    """View medicines in a specific category"""
    category = get_object_or_404(MedicineCategory, id=category_id, active=True)
    
    medicines = Medicine.objects.filter(
        category=category,
        status='available'
    ).annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    ).order_by('-created_at')
    
    # Apply filters
    subcategory_id = request.GET.get('subcategory')
    if subcategory_id:
        medicines = medicines.filter(subcategory_id=subcategory_id)
    
    prescription = request.GET.get('prescription')
    if prescription == 'required':
        medicines = medicines.filter(prescription_required=True)
    elif prescription == 'not_required':
        medicines = medicines.filter(prescription_required=False)
    
    condition = request.GET.get('condition')
    if condition:
        medicines = medicines.filter(condition=condition)
    
    context = {
        'category': category,
        'medicines': medicines,
        'subcategories': category.subcategories.filter(active=True),
    }
    return render(request, 'category_medicines.html', context)


# ============= MEDICINE VERIFICATION =============

@user_passes_test(lambda u: u.is_superuser)
def medicine_verifications(request):
    """Admin view for medicine verifications"""
    verifications = MedicineVerification.objects.select_related(
        'medicine', 'medicine__donor', 'verified_by'
    ).order_by('-created_at')
    
    pending_count = verifications.filter(status='pending').count()
    approved_count = verifications.filter(status='approved').count()
    rejected_count = verifications.filter(status='rejected').count()
    
    context = {
        'verifications': verifications,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'medicine_verifications.html', context)


@user_passes_test(lambda u: u.is_superuser)
def verify_medicine(request, verification_id):
    """Approve or reject medicine verification"""
    verification = get_object_or_404(MedicineVerification, id=verification_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes')
        
        if action == 'approve':
            verification.status = 'approved'
            verification.verified_by = request.user
            verification.verified_at = timezone.now()
            verification.medicine.verified_by_admin = True
            verification.medicine.status = 'available'  # Make available after verification
            verification.medicine.save()
            
            # Notify donor
            Notification.objects.create(
                user=verification.medicine.donor,
                title='Medicine Verified',
                message=f'Your {verification.medicine.name} has been verified and is now available for donation.',
            )
            
        elif action == 'reject':
            verification.status = 'rejected'
            verification.verified_by = request.user
            verification.rejection_reason = request.POST.get('rejection_reason')
            verification.verified_at = timezone.now()
            verification.medicine.status = 'quality_check'
            verification.medicine.save()
            
            # Notify donor
            Notification.objects.create(
                user=verification.medicine.donor,
                title='Medicine Verification Failed',
                message=f'Your {verification.medicine.name} could not be verified. Reason: {verification.rejection_reason}',
            )
        
        verification.notes = notes
        verification.save()
        messages.success(request, f"Medicine {action}d successfully.")
        return redirect('medicine_verifications')
    
    context = {'verification': verification}
    return render(request, 'verify_medicine.html', context)


# ============= INVENTORY MANAGEMENT =============

@login_required
@role_required('ngo')
def ngo_inventory(request):
    """NGO inventory management"""
    if request.user.profile.role != 'ngo':
        return redirect('home')
    
    inventory_items = MedicineInventory.objects.filter(ngo=request.user).select_related('medicine_category')
    
    # Calculate reorder alerts
    from django.db.models import F
    reorder_alerts = inventory_items.filter(
        current_stock__lte=F('minimum_stock_level')
    )
    
    context = {
        'inventory_items': inventory_items,
        'reorder_alerts': reorder_alerts,
        'total_items': inventory_items.count(),
        'low_stock_count': reorder_alerts.count(),
    }
    return render(request, 'ngo_inventory.html', context)


@login_required
@role_required('ngo')
def update_inventory(request, inventory_id):
    """Update inventory stock levels"""
    inventory_item = get_object_or_404(MedicineInventory, id=inventory_id, ngo=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 0))
        
        if action == 'add':
            inventory_item.current_stock += quantity
        elif action == 'subtract':
            inventory_item.current_stock = max(0, inventory_item.current_stock - quantity)
        elif action == 'set':
            inventory_item.current_stock = quantity
        
        inventory_item.save()
        messages.success(request, "Inventory updated successfully.")
        return redirect('ngo_inventory')
    
    context = {'inventory_item': inventory_item}
    return render(request, 'update_inventory.html', context)


# ============= API ENDPOINTS FOR REAL-TIME FEATURES =============

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def api_medicine_search(request):
    """API endpoint for medicine search with filters"""
    query = request.GET.get('q', '')
    category = request.GET.get('category')
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lng')
    radius = request.GET.get('radius', 50)  # km
    
    # Only return non-expired medicines
    medicines = Medicine.objects.filter(status='available').available_only()
    
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query)
        )
    
    if category:
        medicines = medicines.filter(category_id=category)
    
    # Location-based filtering
    if latitude and longitude:
        # Simple distance calculation (for production, use a proper GIS library)
        lat, lng = float(latitude), float(longitude)
        radius_deg = float(radius) / 111  # Rough conversion km to degrees
        
        medicines = medicines.filter(
            latitude__range=(lat - radius_deg, lat + radius_deg),
            longitude__range=(lng - radius_deg, lng + radius_deg)
        )
    
    medicines = medicines.annotate(
        avg_rating=Avg('ratings__rating'),
        ratings_count=Count('ratings')
    )[:50]  # Limit results
    
    data = []
    for med in medicines:
        data.append({
            'id': med.id,
            'name': med.get_display_name(),
            'quantity': med.quantity,
            'unit': med.unit,
            'expiry_date': med.expiry_date,
            'rating': med.rating,
            'rating_count': med.rating_count,
            'latitude': med.latitude,
            'longitude': med.longitude,
            'location_name': med.location_name,
            'category': med.category.name if med.category else None,
            'prescription_required': med.prescription_required,
        })
    
    return Response(data)


@api_view(['GET'])
def api_emergency_alerts(request):
    """API endpoint for emergency alerts"""
    alerts = EmergencyAlert.objects.filter(is_active=True).select_related(
        'ngo', 'medicine_category'
    ).order_by('-priority', '-created_at')[:20]
    
    data = []
    for alert in alerts:
        data.append({
            'id': alert.id,
            'ngo_name': alert.ngo.profile.organization_name,
            'medicine_name': alert.medicine_name,
            'category': alert.medicine_category.name,
            'quantity_needed': alert.quantity_needed,
            'unit': alert.unit,
            'priority': alert.priority,
            'description': alert.description,
            'patient_count': alert.patient_count,
            'deadline': alert.deadline,
            'latitude': alert.latitude,
            'longitude': alert.longitude,
            'location_name': alert.location_name,
            'created_at': alert.created_at,
        })
    
    return Response(data)


def api_subcategories(request):
    """API endpoint for subcategories by category"""
    category_id = request.GET.get('category')
    if category_id:
        subcategories = MedicineSubcategory.objects.filter(category_id=category_id, active=True)
        data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    else:
        data = []
    return JsonResponse(data, safe=False)


# ==================== MESSAGING VIEWS ====================

from .models import Conversation, Message

@login_required
@role_required('ngo', 'donor', 'individual')
def messages_list(request):
    """List all conversations for the current user"""
    if request.user.profile.role == 'ngo':
        conversations = Conversation.objects.filter(ngo=request.user)
    elif request.user.profile.role == 'individual':
        conversations = Conversation.objects.filter(ngo=request.user)
    else:
        conversations = Conversation.objects.filter(donor=request.user)
    
    # Mark all messages as read when viewing conversations list
    Message.objects.filter(
        conversation__in=conversations,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messages_list.html', context)


@login_required
@role_required('ngo', 'donor', 'individual')
def message_detail(request, conv_id):
    """View a specific conversation and send messages (IDOR-protected)"""
    # Prevent IDOR: fetch conversation only if user is part of it
    # Use filter instead of get to prevent information leakage about existence
    conversation = None
    if request.user.profile.role in ['ngo', 'individual']:
        conversation = Conversation.objects.filter(id=conv_id, ngo=request.user).first()
    else:
        conversation = Conversation.objects.filter(id=conv_id, donor=request.user).first()
    
    if not conversation:
        return redirect('messages_list')
    
    # Double-check user is part of conversation (defense in depth)
    if request.user != conversation.donor and request.user != conversation.ngo:
        return redirect('messages_list')
    
    # Mark all messages in this conversation as read
    Message.objects.filter(conversation=conversation, is_read=False).exclude(
        sender=request.user
    ).update(is_read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        message_type = request.POST.get('message_type', 'text')
        new_msg = None

        if message_type == 'location_request':
            # NGO requesting location from donor
            if request.user == conversation.ngo:
                new_msg = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    message_type='location_request',
                    content='📍 Requesting your location for distance calculation',
                )
                conversation.save()
        elif message_type == 'location' and content:
            # Donor sharing location
            try:
                lat, lon = map(float, content.split(','))
                location_name = request.POST.get('location_name', 'Shared Location')
                new_msg = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    message_type='location',
                    content=location_name,
                    location_latitude=lat,
                    location_longitude=lon,
                )
                # Optionally update donor profile with latest shared location
                try:
                    profile = request.user.profile
                    profile.latitude = lat
                    profile.longitude = lon
                    profile.save()
                except:
                    pass
                conversation.save()
            except:
                messages.error(request, 'Invalid location coordinates')
        elif message_type == 'text' and content:
            # Regular text message
            new_msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='text',
                content=content,
            )
            conversation.save()

        # Send email notification to the other party (non-blocking)
        if new_msg:
            try:
                recipient = conversation.get_other_user(request.user)
                if recipient and recipient.email:
                    subject = f"New message on MedShare about {conversation.medicine.name}"
                    convo_url = request.build_absolute_uri(reverse('message_detail', args=[conversation.id]))
                    body = (
                        f"Hi {recipient.get_full_name() or recipient.username},\n\n"
                        f"You have a new message from {request.user.get_full_name() or request.user.username} regarding '{conversation.medicine.name}'.\n\n"
                        f"Open the conversation: {convo_url}\n\n"
                        "Regards,\nMedShare Team"
                    )
                    send_mail(subject, body, getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER), [recipient.email], fail_silently=True)
            except Exception:
                # Don't let email errors block messaging
                pass

        return redirect('message_detail', conv_id=conversation.id)
    
    messages_list = conversation.messages.all()
    other_user = conversation.get_other_user(request.user)
    
    # Get current user's location for distance calculation
    user_location = None
    if request.user.profile.latitude and request.user.profile.longitude:
        user_location = (request.user.profile.latitude, request.user.profile.longitude)
    
    # Pre-calculate distances for location messages
    for msg in messages_list:
        msg.distance = None
        if msg.message_type == 'location' and user_location:
            msg.distance = msg.get_distance_to(user_location[0], user_location[1])
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_user': other_user,
        'other_user_role': conversation.get_other_user_role(request.user),
        'medicine': conversation.medicine,
        'user_location': user_location,
    }
    return render(request, 'message_detail.html', context)


@login_required
@role_required('ngo', 'donor', 'individual')
def start_conversation(request, med_id):
    """Start or get existing conversation between user and donor"""
    # Only NGOs and individuals can initiate conversations with donors
    if request.user.profile.role not in ['ngo', 'individual']:
        return redirect('home')
    
    # Get medicine (verify it exists and is available, prevent IDOR)
    try:
        medicine = Medicine.objects.get(id=med_id, status='available')
        donor = medicine.donor
        ngo = request.user
    except Medicine.DoesNotExist:
        return redirect('home')
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        medicine=medicine,
        donor=donor,
        ngo=ngo,
    )
    
    return redirect('message_detail', conv_id=conversation.id)


def privacy(request):
    """Privacy Policy page"""
    return render(request, 'privacy.html')


def terms(request):
    """Terms of Service page"""
    return render(request, 'terms.html')

