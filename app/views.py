from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
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
    MedicineSearchLog, Notification, ContactMessage, Testimonial, FAQ, PasswordResetToken
)
from .forms import (
    MedicineForm, UserSignupForm, UserProfileForm, UserLoginForm,
    DonationRequestForm, MedicineRatingForm, MedicineSearchForm,
    ContactMessageForm, ForgotPasswordForm, ResetPasswordForm, TestimonialForm
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

