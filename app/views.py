from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Count
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

from .models import (
    Medicine, DonationRequest, UserProfile, MedicineRating,
    MedicineSearchLog, Notification, ContactMessage, Testimonial, FAQ, PasswordResetToken,
    PickupDelivery, DeliveryBoy, Delivery, DeliveryLocation,
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
@csrf_exempt
def add_medicine(request):
    """Add new medicine donation"""
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
def expiry_tracker(request):
    """Real-time expiry tracker showing all medicines with countdown"""
    if request.user.profile.role == 'donor':
        medicines = Medicine.objects.filter(donor=request.user, status='available')
    else:
        medicines = Medicine.objects.filter(status='available')

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
    writer.writerow(['Medicine Name', 'Donor', 'NGO', 'Status', 'Date'])
    for req in DonationRequest.objects.select_related('medicine', 'medicine__donor', 'ngo'):
        writer.writerow([
            req.medicine.name,
            req.medicine.donor.username,
            req.ngo.username,
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
def pickup_delivery_dashboard(request):
    """Pickup and Delivery tracking dashboard for donors and NGOs"""
    user_profile = request.user.profile
    pickups = PickupDelivery.objects.none()
    stats = {}
    
    if user_profile.role == 'donor':
        # Donor view - pickups they need to do
        pickups = PickupDelivery.objects.filter(donor=request.user).annotate(
            avg_rating=Avg('medicine__ratings__rating')
        )
        stats = {
            'pending_pickups': pickups.filter(status='pending').count(),
            'picked_up': pickups.filter(status='picked_up').count(),
            'in_transit': pickups.filter(status='in_transit').count(),
            'total': pickups.count(),
        }
    elif user_profile.role == 'ngo':
        # NGO view - deliveries they should receive
        pickups = PickupDelivery.objects.filter(ngo=request.user).annotate(
            avg_rating=Avg('medicine__ratings__rating')
        )
        stats = {
            'pending_delivery': pickups.filter(status='pending').count(),
            'in_transit': pickups.filter(status='in_transit').count(),
            'delivered': pickups.filter(status='delivered').count(),
            'total': pickups.count(),
        }
    
    context = {
        'pickups': pickups,
        'stats': stats,
        'user_role': user_profile.role,
    }
    return render(request, 'pickup_delivery_dashboard.html', context)


@login_required
def create_pickup_delivery(request, req_id):
    """Create pickup and delivery tracking from donation request"""
    donation_req = get_object_or_404(DonationRequest, id=req_id, status='accepted')
    user_profile = request.user.profile
    
    # Only donor can create pickup/delivery
    if donation_req.medicine.donor != request.user:
        messages.error(request, "You don't have permission to create this pickup record.")
        return redirect('donor_dashboard')
    
    # Check if already exists
    if hasattr(donation_req, 'pickup_delivery'):
        messages.info(request, "Pickup/Delivery record already exists for this request.")
        return redirect('pickup_delivery_detail', pd_id=donation_req.pickup_delivery.id)
    
    if request.method == 'POST':
        scheduled_date = request.POST.get('scheduled_pickup_date')
        notes = request.POST.get('pickup_notes')
        quantity = donation_req.quantity_requested or donation_req.medicine.quantity
        
        pickup_delivery = PickupDelivery.objects.create(
            donation_request=donation_req,
            donor=request.user,
            ngo=donation_req.ngo,
            medicine=donation_req.medicine,
            status='pending',
            scheduled_pickup_date=scheduled_date if scheduled_date else None,
            pickup_notes=notes,
            quantity_scheduled=quantity
        )
        
        messages.success(request, "Pickup and delivery tracking created successfully.")
        return redirect('pickup_delivery_detail', pd_id=pickup_delivery.id)
    
    context = {
        'donation_request': donation_req,
        'medicine': donation_req.medicine,
    }
    return render(request, 'create_pickup_delivery.html', context)


@login_required
def pickup_delivery_detail(request, pd_id):
    """View and update pickup/delivery details"""
    pickup_delivery = get_object_or_404(PickupDelivery, id=pd_id)
    user_profile = request.user.profile
    
    # Only donor or NGO involved can view
    if request.user != pickup_delivery.donor and request.user != pickup_delivery.ngo:
        messages.error(request, "You don't have permission to view this.")
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_picked_up' and user_profile.role == 'donor':
            pickup_delivery.status = 'picked_up'
            pickup_delivery.pickup_date = timezone.now()
            pickup_delivery.quantity_picked_up = int(request.POST.get('quantity_picked_up', 0))
            pickup_delivery.pickup_notes = request.POST.get('pickup_notes', '')
            pickup_delivery.save()
            messages.success(request, "Medicine marked as picked up.")
            
            # Notify NGO
            Notification.objects.create(
                user=pickup_delivery.ngo,
                title='Medicine Picked Up',
                message=f'{pickup_delivery.medicine.name} has been picked up by the donor.'
            )
        
        elif action == 'mark_in_transit' and user_profile.role == 'donor':
            if pickup_delivery.status == 'picked_up':
                pickup_delivery.status = 'in_transit'
                pickup_delivery.save()
                messages.success(request, "Medicine marked as in transit.")
                
                # Notify NGO
                Notification.objects.create(
                    user=pickup_delivery.ngo,
                    title='Medicine In Transit',
                    message=f'{pickup_delivery.medicine.name} is now in transit to your facility.'
                )
        
        elif action == 'mark_delivered' and user_profile.role == 'ngo':
            if pickup_delivery.status in ['in_transit', 'picked_up']:
                pickup_delivery.status = 'delivered'
                pickup_delivery.delivery_date = timezone.now()
                pickup_delivery.quantity_delivered = int(request.POST.get('quantity_delivered', 0))
                pickup_delivery.delivery_notes = request.POST.get('delivery_notes', '')
                pickup_delivery.save()
                messages.success(request, "Medicine marked as delivered.")
                
                # Update donation request status
                pickup_delivery.donation_request.status = 'completed'
                pickup_delivery.donation_request.completed_at = timezone.now()
                pickup_delivery.donation_request.save()
                
                # Notify donor
                Notification.objects.create(
                    user=pickup_delivery.donor,
                    title='Medicine Delivered',
                    message=f'{pickup_delivery.medicine.name} has been successfully delivered to {pickup_delivery.ngo.profile.organization_name}.'
                )
        
        elif action == 'cancel' and user_profile.role in ['donor', 'ngo']:
            pickup_delivery.status = 'cancelled'
            pickup_delivery.save()
            messages.success(request, "Pickup/Delivery cancelled.")
        
        return redirect('pickup_delivery_detail', pd_id=pd_id)
    
    context = {
        'pickup_delivery': pickup_delivery,
        'can_update_pickup': user_profile.role == 'donor',
        'can_update_delivery': user_profile.role == 'ngo',
    }
    return render(request, 'pickup_delivery_detail.html', context)


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


def find_nearest_delivery_boy(donor_lat, donor_lon, exclude_busy=True):
    """
    Find the nearest available delivery boy using Haversine formula.
    Returns the closest DeliveryBoy object or None.
    """
    if exclude_busy:
        delivery_boys = DeliveryBoy.objects.filter(is_available='available', verified=True)
    else:
        delivery_boys = DeliveryBoy.objects.filter(verified=True)
    
    if not delivery_boys.exists():
        return None
    
    min_distance = float('inf')
    nearest_boy = None
    
    for boy in delivery_boys:
        if boy.current_latitude and boy.current_longitude:
            distance = haversine_distance(
                donor_lat, donor_lon,
                boy.current_latitude, boy.current_longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_boy = boy
    
    return nearest_boy


@login_required
def delivery_boy_dashboard(request):
    """
    Delivery boy dashboard showing assigned deliveries and statistics.
    """
    try:
        delivery_boy = request.user.delivery_boy
    except DeliveryBoy.DoesNotExist:
        messages.error(request, "You are not registered as a delivery boy.")
        return redirect('home')
    
    # Get assigned deliveries
    deliveries = Delivery.objects.filter(
        delivery_boy=delivery_boy
    ).select_related('pickup_delivery__medicine', 'pickup_delivery__donor', 'pickup_delivery__ngo').annotate(
        avg_rating=Avg('rating')
    )
    
    # Statistics
    stats = {
        'active': deliveries.filter(status__in=['assigned', 'picked_up', 'in_transit']).count(),
        'completed': deliveries.filter(status='delivered').count(),
        'total': deliveries.count(),
        'rating': delivery_boy.rating,
        'completion_rate': delivery_boy.get_completion_rate(),
    }
    
    context = {
        'delivery_boy': delivery_boy,
        'deliveries': deliveries,
        'stats': stats,
    }
    return render(request, 'delivery_boy_dashboard.html', context)


@login_required
def delivery_detail(request, delivery_id):
    """
    Delivery detail view for delivery boy to update status and location.
    """
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Only delivery boy assigned to this delivery can view it
    if request.user != delivery.delivery_boy.user:
        messages.error(request, "You don't have permission to view this delivery.")
        return redirect('delivery_boy_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_picked_up':
            delivery.status = 'picked_up'
            delivery.picked_up_at = timezone.now()
            delivery.save()
            
            # Notify NGO
            Notification.objects.create(
                user=delivery.pickup_delivery.ngo,
                title='Medicine Picked Up',
                message=f'{delivery.pickup_delivery.medicine.name} has been picked up.',
                donation_request=delivery.pickup_delivery.donation_request
            )
            messages.success(request, "Medicine marked as picked up.")
        
        elif action == 'start_transit':
            delivery.status = 'in_transit'
            delivery.started_at = timezone.now()
            delivery.save()
            
            # Notify NGO
            Notification.objects.create(
                user=delivery.pickup_delivery.ngo,
                title='Medicine In Transit',
                message=f'{delivery.pickup_delivery.medicine.name} is on the way.',
                donation_request=delivery.pickup_delivery.donation_request
            )
            messages.success(request, "Delivery started.")
        
        elif action == 'mark_delivered':
            delivery.status = 'delivered'
            delivery.delivered_at = timezone.now()
            # Update delivery boy stats
            delivery.delivery_boy.completed_deliveries += 1
            delivery.delivery_boy.total_deliveries += 1
            delivery.delivery_boy.save()
            delivery.save()
            
            # Update pickup delivery status
            delivery.pickup_delivery.status = 'delivered'
            delivery.pickup_delivery.save()
            
            # Notify NGO
            Notification.objects.create(
                user=delivery.pickup_delivery.ngo,
                title='Medicine Delivered',
                message=f'{delivery.pickup_delivery.medicine.name} has been delivered.',
                donation_request=delivery.pickup_delivery.donation_request
            )
            messages.success(request, "Delivery marked as completed.")
        
        return redirect('delivery_detail', delivery_id=delivery_id)
    
    # Get location history
    locations = delivery.locations.all()
    
    context = {
        'delivery': delivery,
        'pickup_delivery': delivery.pickup_delivery,
        'locations': locations,
    }
    return render(request, 'delivery_detail.html', context)


@login_required
def delivery_assign(request):
    """
    Admin view to assign delivery boys to pending pickups.
    Shows list of pending pickups and available delivery boys.
    """
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.error(request, "You don't have permission to assign deliveries.")
        return redirect('home')
    
    # Get pickups without assignments
    pending_pickups = PickupDelivery.objects.filter(
        status__in=['pending', 'picked_up']
    ).filter(
        delivery__isnull=True
    ).select_related('medicine__donor', 'ngo', 'donor')
    
    if request.method == 'POST':
        pickup_id = request.POST.get('pickup_id')
        delivery_boy_id = request.POST.get('delivery_boy_id')
        
        pickup = get_object_or_404(PickupDelivery, id=pickup_id)
        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)
        
        # Create delivery record
        delivery = Delivery.objects.create(
            pickup_delivery=pickup,
            delivery_boy=delivery_boy,
            status='assigned'
        )
        
        # Mark delivery boy as busy
        delivery_boy.is_available = 'busy'
        delivery_boy.save()
        
        # Create notification
        Notification.objects.create(
            user=delivery_boy.user,
            title='New Delivery Assigned',
            message=f'You have been assigned to deliver {pickup.medicine.name}'
        )
        
        messages.success(request, f"Delivery assigned to {delivery_boy.user.first_name}")
        return redirect('delivery_assign')
    
    # Available delivery boys
    available_boys = DeliveryBoy.objects.filter(is_available='available', verified=True)
    
    context = {
        'pending_pickups': pending_pickups,
        'available_boys': available_boys,
    }
    return render(request, 'delivery_assign.html', context)


@login_required
def delivery_track_admin(request, delivery_id):
    """
    Admin view to track delivery progress with live map.
    """
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if not request.user.is_superuser and request.user.profile.role != 'admin':
        messages.error(request, "You don't have permission to view this.")
        return redirect('home')
    
    locations = delivery.locations.all()
    
    context = {
        'delivery': delivery,
        'pickup_delivery': delivery.pickup_delivery,
        'locations': locations,
    }
    return render(request, 'delivery_track_admin.html', context)


@login_required
def delivery_track_ngo(request, delivery_id):
    """
    NGO view to track delivery progress with live map.
    """
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if request.user != delivery.pickup_delivery.ngo:
        messages.error(request, "You don't have permission to view this delivery.")
        return redirect('home')
    
    locations = delivery.locations.all()
    
    context = {
        'delivery': delivery,
        'pickup_delivery': delivery.pickup_delivery,
        'locations': locations,
    }
    return render(request, 'delivery_track_ngo.html', context)


# ============================================
# AJAX/API ENDPOINTS FOR LIVE TRACKING
# ============================================

@login_required
@require_POST
def update_location(request, delivery_id):
    """
    AJAX endpoint to update delivery boy's current location.
    Accepts JSON with latitude and longitude.
    """
    try:
        delivery = get_object_or_404(Delivery, id=delivery_id)
        
        # Only the assigned delivery boy can update location
        if request.user != delivery.delivery_boy.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get coordinates from POST request
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        accuracy = request.POST.get('accuracy')
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        # Create location record
        location = DeliveryLocation.objects.create(
            delivery=delivery,
            latitude=latitude,
            longitude=longitude,
            accuracy=float(accuracy) if accuracy else None
        )
        
        # Update delivery boy's current location
        delivery.delivery_boy.current_latitude = latitude
        delivery.delivery_boy.current_longitude = longitude
        delivery.delivery_boy.last_location_update = timezone.now()
        delivery.delivery_boy.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Location updated',
            'location_id': location.id,
            'timestamp': location.timestamp.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_delivery_locations(request, delivery_id):
    """
    AJAX endpoint to get all locations for a delivery (for map visualization).
    Returns JSON list of coordinates.
    """
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Check permissions
    can_view = (
        request.user.is_superuser or 
        request.user == delivery.delivery_boy.user or 
        request.user == delivery.pickup_delivery.ngo
    )
    
    if not can_view:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    locations = delivery.locations.all().values('id', 'latitude', 'longitude', 'timestamp')
    
    return JsonResponse({
        'delivery_id': delivery_id,
        'status': delivery.status,
        'locations': list(locations),
        'delivery_boy': {
            'name': delivery.delivery_boy.user.get_full_name() or delivery.delivery_boy.user.username,
            'phone': delivery.delivery_boy.phone,
            'vehicle': delivery.delivery_boy.get_vehicle_type_display(),
        },
        'medicine': {
            'name': delivery.pickup_delivery.medicine.name,
            'quantity': delivery.pickup_delivery.quantity_scheduled,
        }
    })


@login_required
def get_delivery_status(request, delivery_id):
    """
    AJAX endpoint to get current delivery status.
    """
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Check permissions
    can_view = (
        request.user.is_superuser or 
        request.user == delivery.delivery_boy.user or 
        request.user == delivery.pickup_delivery.ngo
    )
    
    if not can_view:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    last_location = delivery.locations.first()
    
    return JsonResponse({
        'delivery_id': delivery_id,
        'status': delivery.status,
        'status_display': delivery.get_status_display(),
        'delivery_boy_name': delivery.delivery_boy.user.get_full_name() or delivery.delivery_boy.user.username,
        'current_location': {
            'latitude': last_location.latitude if last_location else None,
            'longitude': last_location.longitude if last_location else None,
            'timestamp': last_location.timestamp.isoformat() if last_location else None,
        },
        'assigned_at': delivery.assigned_at.isoformat(),
        'picked_up_at': delivery.picked_up_at.isoformat() if delivery.picked_up_at else None,
        'delivered_at': delivery.delivered_at.isoformat() if delivery.delivered_at else None,
    })
 
# ============= EMERGENCY ALERTS =============

@login_required
def emergency_alerts(request):
    """View all active emergency alerts"""
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

    context = {
        'alerts': alerts,
        'total_alerts': alerts.count(),
        'critical_alerts': alerts.filter(priority='critical').count(),
    }
    return render(request, 'emergency_alerts.html', context)


@login_required
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
            
            # Create notifications for donors who have similar medicines
            similar_medicines = Medicine.objects.filter(
                category=category,
                status='available',
                donor__profile__preferred_contact_method__in=['email', 'both']
            )
            
            for medicine in similar_medicines[:10]:  # Limit to 10 donors
                Notification.objects.create(
                    user=medicine.donor,
                    title='Emergency Medicine Alert',
                    message=f'Urgent need for {medicine_name} at {request.user.profile.organization_name}. Priority: {priority.upper()}',
                )
            
            messages.success(request, "Emergency alert created successfully!")
            return redirect('emergency_alerts')
            
        except Exception as e:
            messages.error(request, f"Error creating alert: {str(e)}")
    
    categories = MedicineCategory.objects.filter(active=True)
    context = {'categories': categories}
    return render(request, 'create_emergency_alert.html', context)


@login_required
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
def ngo_inventory(request):
    """NGO inventory management"""
    if request.user.profile.role != 'ngo':
        return redirect('home')
    
    inventory_items = MedicineInventory.objects.filter(ngo=request.user).select_related('medicine_category')
    
    # Calculate reorder alerts
    reorder_alerts = inventory_items.filter(
        current_stock__lte=models.F('minimum_stock_level')
    )
    
    context = {
        'inventory_items': inventory_items,
        'reorder_alerts': reorder_alerts,
        'total_items': inventory_items.count(),
        'low_stock_count': reorder_alerts.count(),
    }
    return render(request, 'ngo_inventory.html', context)


@login_required
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
    
    medicines = Medicine.objects.filter(status='available')
    
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

