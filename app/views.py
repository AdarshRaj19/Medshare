from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date, timedelta
from math import radians, cos, sin, asin, sqrt

from .models import (
    Medicine, DonationRequest, UserProfile, MedicineRating, 
    MedicineSearchLog, Notification
)
from .forms import (
    MedicineForm, UserSignupForm, UserProfileForm, UserLoginForm,
    DonationRequestForm, MedicineRatingForm, MedicineSearchForm
)
from .recommender import MedicineRecommender


def home(request):
    """Home page with statistics and featured medicines"""
    total_medicines = Medicine.objects.filter(status='available').count()
    total_donors = User.objects.filter(profile__role='donor').count()
    total_ngos = User.objects.filter(profile__role='ngo').count()
    
    # Featured medicines (highly rated)
    featured = Medicine.objects.filter(
        status='available'
    ).annotate(
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
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create or update user profile. A post_save signal may already
            # have created the profile when the user was saved, so use
            # update_or_create to avoid UNIQUE constraint failures.
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': form.cleaned_data['role'],
                    'phone': form.cleaned_data.get('phone'),
                    'organization_name': form.cleaned_data.get('organization_name'),
                }
            )

            # Log the user in
            login(request, user)
            messages.success(request, "Account created successfully. Welcome to MedShare!")

            # Redirect based on role
            if form.cleaned_data['role'] == 'donor':
                return redirect('donor_dashboard')
            else:
                return redirect('ngo_dashboard')
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
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")

                if user.is_superuser:
                    return redirect('admin_reports')
                
                try:
                    role = user.profile.role
                    if role == 'donor':
                        return redirect('donor_dashboard')
                    else:
                        return redirect('ngo_dashboard')
                except UserProfile.DoesNotExist:
                    return redirect('home')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    """User logout"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def user_profile(request):
    """View and edit user profile"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    # Stats for profile page
    donor_stats = None
    ngo_stats = None
    if profile.role == "donor":
        donor_meds = Medicine.objects.filter(donor=request.user)
        donor_stats = {
            "total_medicines": donor_meds.count(),
            "active_medicines": donor_meds.filter(status="available").count(),
            "medicines_donated": donor_meds.filter(status="donated").count(),
            "total_ratings": MedicineRating.objects.filter(medicine__donor=request.user).count(),
        }
    elif profile.role == "ngo":
        ngo_reqs = DonationRequest.objects.filter(ngo=request.user)
        ngo_stats = {
            "requests_made": ngo_reqs.count(),
            "pending_requests": ngo_reqs.filter(status="pending").count(),
            "medicines_received": ngo_reqs.filter(status="completed").count(),
        }

    context = {
        'form': form,
        'profile': profile,
        'donor_stats': donor_stats,
        'ngo_stats': ngo_stats,
    }
    return render(request, 'user_profile.html', context)


@login_required
def donor_dashboard(request):
    """Donor dashboard - list of donated medicines"""
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
    donated = medicines.filter(status='donated').count()

    context = {
        'medicines': medicines,
        'total': total,
        'available': available,
        'donated': donated,
    }
    return render(request, 'donor_dashboard.html', context)


@login_required
def edit_medicine(request, med_id):
    """Edit an existing medicine donation (donor-only, owner-only)."""
    medicine = get_object_or_404(Medicine, id=med_id, donor=request.user)

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
@require_POST
def delete_medicine(request, med_id):
    """Delete a medicine donation (donor-only, owner-only)."""
    medicine = get_object_or_404(Medicine, id=med_id, donor=request.user)
    medicine.delete()
    messages.success(request, "Medicine deleted.")
    return redirect("donor_dashboard")


@login_required
def add_medicine(request):
    """Add new medicine donation"""
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            med = form.save(commit=False)
            med.donor = request.user
            med.save()
            messages.success(request, "Medicine listed for donation.")
            return redirect('donor_dashboard')
    else:
        form = MedicineForm()

    return render(request, 'add_medicine.html', {'form': form})


@login_required
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


@login_required
def rate_medicine(request, med_id):
    """Rate a medicine"""
    medicine = get_object_or_404(Medicine, id=med_id)

    if request.method == 'POST':
        form = MedicineRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.medicine = medicine
            rating.save()

            # Update medicine rating
            avg = medicine.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
            medicine.rating = round(avg, 2)
            medicine.rating_count = medicine.ratings.count()
            medicine.save()

            return redirect('medicine_detail', med_id=med_id)
    else:
        form = MedicineRatingForm()

    return render(request, 'rate_medicine.html', {'form': form, 'medicine': medicine})


@login_required
def ngo_dashboard(request):
    """NGO dashboard - search and request medicines"""
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

    # Statistics
    requests_pending = DonationRequest.objects.filter(
        ngo=request.user,
        status='pending'
    ).count()
    received_count = DonationRequest.objects.filter(
        ngo=request.user,
        status='completed'
    ).count()

    context = {
        'medicines': medicines,
        'form': form,
        'requests_pending': requests_pending,
        'received_count': received_count,
    }
    # AI recommendations
    try:
        context["ai_recommendations"] = MedicineRecommender(request.user).get_ngo_recommendations(limit=6)
    except Exception:
        context["ai_recommendations"] = []
    return render(request, 'ngo_dashboard.html', context)


@login_required
def request_medicine(request, med_id):
    """Request a medicine"""
    medicine = get_object_or_404(Medicine, id=med_id)

    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation_req = form.save(commit=False)
            donation_req.medicine = medicine
            donation_req.ngo = request.user
            donation_req.save()

            # Create notification for donor
            Notification.objects.create(
                user=medicine.donor,
                title='Medicine Request',
                message=f"{request.user.first_name or request.user.username} requested {medicine.name}",
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
def donation_request_detail(request, req_id):
    """View donation request details"""
    donation_req = get_object_or_404(DonationRequest, id=req_id)

    # Check permissions
    if request.user != donation_req.ngo and request.user != donation_req.medicine.donor:
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept' and request.user == donation_req.medicine.donor:
            donation_req.status = 'accepted'
            donation_req.save()

            # Create notification
            Notification.objects.create(
                user=donation_req.ngo,
                title='Request Accepted',
                message=f"Your request for {donation_req.medicine.name} has been accepted",
                donation_request=donation_req
            )

        elif action == 'reject' and request.user == donation_req.medicine.donor:
            donation_req.status = 'rejected'
            donation_req.save()

            # Create notification
            Notification.objects.create(
                user=donation_req.ngo,
                title='Request Rejected',
                message=f"Your request for {donation_req.medicine.name} has been rejected",
                donation_request=donation_req
            )

        elif action == 'complete' and request.user == donation_req.medicine.donor:
            donation_req.status = 'completed'
            donation_req.completed_at = date.today()
            donation_req.medicine.status = 'donated'
            donation_req.medicine.save()
            donation_req.save()

            # Create notification
            Notification.objects.create(
                user=donation_req.ngo,
                title='Request Completed',
                message=f"Your request for {donation_req.medicine.name} has been completed",
                donation_request=donation_req
            )

    context = {
        'donation_request': donation_req,
        'medicine': donation_req.medicine,
    }
    return render(request, 'donation_request_detail.html', context)


@login_required
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


@user_passes_test(is_admin)
def admin_reports(request):
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
