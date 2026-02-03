from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import re
from .models import (
    Medicine, UserProfile, DonationRequest, MedicineRating,
    ContactMessage, Testimonial, MedicineCategory, MedicineSubcategory,
    EmergencyAlert, BulkDonationRequest, BulkDonationItem, MedicineVerification,
    MedicineInventory
)


class MedicineForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=MedicineCategory.objects.filter(active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Medicine Category'
    )
    subcategory = forms.ModelChoiceField(
        queryset=MedicineSubcategory.objects.filter(active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Subcategory'
    )
    
    class Meta:
        model = Medicine
        fields = [
            'name', 'quantity', 'category',
            'condition', 'expiry_date', 
            'location_name', 'latitude', 'longitude',
            'brand_name', 'generic_name', 'manufacture_date', 'batch_number', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine Name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': date.today().isoformat()}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name (e.g., Tylenol)'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Generic Name (e.g., Paracetamol)'}),
            'manufacture_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': date.today().isoformat()}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch/Lot Number'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.0001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.0001'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location Name'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter subcategories based on selected category
        if self.instance and self.instance.category:
            self.fields['subcategory'].queryset = MedicineSubcategory.objects.filter(
                category=self.instance.category, active=True
            )
        else:
            self.fields['subcategory'].queryset = MedicineSubcategory.objects.none()

        # Make the less-important "advanced" fields optional in the form
        optional_fields = ['brand_name', 'manufacture_date', 'batch_number', 'image']
        for fname in optional_fields:
            if fname in self.fields:
                self.fields[fname].required = False

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Medicine name must be at least 2 characters long.")
        if name and not re.match(r'^[a-zA-Z\s\-()]+$', name):
            raise forms.ValidationError("Medicine name should contain only letters, spaces, hyphens, and parentheses.")
        return name

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError("Quantity must be a positive number.")
        if quantity and quantity > 999999:
            raise forms.ValidationError("Quantity cannot exceed 999,999.")
        return quantity

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < date.today():
            raise forms.ValidationError("Expiry date must be today or in the future.")
        return expiry_date

    def clean_manufacture_date(self):
        manufacture_date = self.cleaned_data.get('manufacture_date')
        if manufacture_date and manufacture_date > date.today():
            raise forms.ValidationError("Manufacture date cannot be in the future.")
        return manufacture_date

    def clean_brand_name(self):
        brand_name = self.cleaned_data.get('brand_name')
        if brand_name and len(brand_name.strip()) < 2:
            raise forms.ValidationError("Brand name must be at least 2 characters long.")
        return brand_name

    def clean_generic_name(self):
        generic_name = self.cleaned_data.get('generic_name')
        if generic_name and len(generic_name.strip()) < 2:
            raise forms.ValidationError("Generic name must be at least 2 characters long.")
        return generic_name

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude and (latitude < -90 or latitude > 90):
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude and (longitude < -180 or longitude > 180):
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def clean_location_name(self):
        location_name = self.cleaned_data.get('location_name')
        if location_name and len(location_name.strip()) < 2:
            raise forms.ValidationError("Location name must be at least 2 characters long.")
        return location_name

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        expiry_date = cleaned_data.get('expiry_date')
        manufacture_date = cleaned_data.get('manufacture_date')
        
        if subcategory and category and subcategory.category != category:
            raise forms.ValidationError("Selected subcategory does not belong to the selected category.")
        
        if manufacture_date and expiry_date and manufacture_date >= expiry_date:
            raise forms.ValidationError("Manufacture date must be before the expiry date.")
        
        # Check if medicine name is too similar to existing ones (optional duplicate check)
        name = cleaned_data.get('name')
        if name and self.instance.pk is None:  # Only for new medicines
            similar = Medicine.objects.filter(name__iexact=name).exists()
            if similar:
                raise forms.ValidationError("A medicine with this name already exists. Please check before adding.")
        
        return cleaned_data


class UserSignupForm(UserCreationForm):
    # UserCreationForm already provides password1 and password2
    role = forms.ChoiceField(
        choices=[('donor', 'Medicine Donor'), ('individual', 'Individual/Patient'), ('ngo', 'NGO/Hospital')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    organization_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization Name (for NGOs)'}),
        label='Organization Name'
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        label='Phone Number'
    )

    # Override password fields to add form-control class
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 3:
                raise forms.ValidationError("Username must be at least 3 characters long.")
            if len(username) > 30:
                raise forms.ValidationError("Username cannot exceed 30 characters.")
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                raise forms.ValidationError("Username can only contain letters, numbers, and underscores.")
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                raise forms.ValidationError("Please enter a valid email address.")
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("This email is already registered.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name and len(first_name.strip()) < 2:
            raise forms.ValidationError("First name must be at least 2 characters long.")
        if first_name and len(first_name) > 50:
            raise forms.ValidationError("First name cannot exceed 50 characters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and len(last_name.strip()) < 2:
            raise forms.ValidationError("Last name must be at least 2 characters long.")
        if last_name and len(last_name) > 50:
            raise forms.ValidationError("Last name cannot exceed 50 characters.")
        return last_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common formatting characters
            cleaned_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
            if len(cleaned_phone) < 7:
                raise forms.ValidationError("Phone number must be at least 7 digits.")
            if len(cleaned_phone) > 20:
                raise forms.ValidationError("Phone number is too long.")
            if not any(char.isdigit() for char in cleaned_phone):
                raise forms.ValidationError("Phone number must contain at least one digit.")
        return phone

    def clean_organization_name(self):
        organization_name = self.cleaned_data.get('organization_name')
        role = self.cleaned_data.get('role')
        
        if role == 'ngo' and not organization_name:
            raise forms.ValidationError("Organization name is required for NGO/Hospital accounts.")
        
        if organization_name and len(organization_name.strip()) < 2:
            raise forms.ValidationError("Organization name must be at least 2 characters long.")
        
        return organization_name

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match!")
            
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            
            # Check password complexity
            has_letter = any(char.isalpha() for char in password1)
            has_digit = any(char.isdigit() for char in password1)
            
            if not (has_letter and has_digit):
                raise forms.ValidationError("Password must contain both letters and numbers.")
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'organization_name', 'latitude', 'longitude', 'bio', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
            if len(cleaned_phone) < 7:
                raise forms.ValidationError("Phone number must be at least 7 digits.")
            if len(cleaned_phone) > 20:
                raise forms.ValidationError("Phone number is too long.")
            if not any(char.isdigit() for char in cleaned_phone):
                raise forms.ValidationError("Phone number must contain at least one digit.")
        return phone

    def clean_organization_name(self):
        organization_name = self.cleaned_data.get('organization_name')
        if organization_name and len(organization_name.strip()) < 2:
            raise forms.ValidationError("Organization name must be at least 2 characters long.")
        if organization_name and len(organization_name) > 100:
            raise forms.ValidationError("Organization name cannot exceed 100 characters.")
        return organization_name

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None:
            if latitude < -90 or latitude > 90:
                raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None:
            if longitude < -180 or longitude > 180:
                raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) > 500:
            raise forms.ValidationError("Bio cannot exceed 500 characters.")
        return bio

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Profile picture cannot exceed 5 MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                raise forms.ValidationError("Only JPEG, PNG, GIF, and WebP images are allowed.")
        
        return profile_picture


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and len(username.strip()) == 0:
            raise forms.ValidationError("Username cannot be empty.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password.strip()) == 0:
            raise forms.ValidationError("Password cannot be empty.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            if len(username) < 3:
                raise forms.ValidationError("Invalid username or password.")
            if len(password) < 1:
                raise forms.ValidationError("Invalid username or password.")
        
        return cleaned_data


class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['quantity_requested', 'message']
        widgets = {
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity Needed'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Message to Donor'}),
        }

    def clean_quantity_requested(self):
        quantity_requested = self.cleaned_data.get('quantity_requested')
        if quantity_requested and quantity_requested <= 0:
            raise forms.ValidationError("Quantity must be a positive number.")
        if quantity_requested and quantity_requested > 999999:
            raise forms.ValidationError("Quantity cannot exceed 999,999.")
        return quantity_requested

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 5:
            raise forms.ValidationError("Message must be at least 5 characters long.")
        if message and len(message) > 1000:
            raise forms.ValidationError("Message cannot exceed 1000 characters.")
        return message


class MedicineRatingForm(forms.ModelForm):
    class Meta:
        model = MedicineRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} Stars') for i in range(1, 6)],
                attrs={'class': 'form-check-input'}
            ),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your feedback'}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating:
            if rating < 1 or rating > 5:
                raise forms.ValidationError("Rating must be between 1 and 5 stars.")
        return rating

    def clean_review(self):
        review = self.cleaned_data.get('review')
        if review and len(review.strip()) < 5:
            raise forms.ValidationError("Review must be at least 5 characters long.")
        if review and len(review) > 500:
            raise forms.ValidationError("Review cannot exceed 500 characters.")
        return review


class MedicineSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search medicines...'
        })
    )
    expiring_soon = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Show expiring soon (within 30 days)'
    )
    rating_min = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5', 'step': '0.5'}),
        label='Minimum Rating'
    )

    def clean_query(self):
        query = self.cleaned_data.get('query')
        if query and len(query.strip()) > 100:
            raise forms.ValidationError("Search query cannot exceed 100 characters.")
        return query

    def clean_rating_min(self):
        rating_min = self.cleaned_data.get('rating_min')
        if rating_min is not None:
            if rating_min < 0 or rating_min > 5:
                raise forms.ValidationError("Minimum rating must be between 0 and 5.")
        return rating_min


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your Message'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        if name and len(name) > 100:
            raise forms.ValidationError("Name cannot exceed 100 characters.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if subject and len(subject.strip()) < 3:
            raise forms.ValidationError("Subject must be at least 3 characters long.")
        if subject and len(subject) > 100:
            raise forms.ValidationError("Subject cannot exceed 100 characters.")
        return subject

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        if message and len(message) > 2000:
            raise forms.ValidationError("Message cannot exceed 2000 characters.")
        return message


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise forms.ValidationError("Please enter a valid email address.")
        return email


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}),
        label='New Password'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            
            has_letter = any(char.isalpha() for char in password)
            has_digit = any(char.isdigit() for char in password)
            
            if not (has_letter and has_digit):
                raise forms.ValidationError("Password must contain both letters and numbers.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'role', 'message', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your story...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        if name and len(name) > 100:
            raise forms.ValidationError("Name cannot exceed 100 characters.")
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        if message and len(message) > 1000:
            raise forms.ValidationError("Message cannot exceed 1000 characters.")
        return message

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image cannot exceed 5 MB.")
            
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_types:
                raise forms.ValidationError("Only JPEG, PNG, GIF, and WebP images are allowed.")
        
        return image


# ============= NEW FORMS FOR ENHANCED FEATURES =============

class EmergencyAlertForm(forms.ModelForm):
    class Meta:
        model = EmergencyAlert
        fields = [
            'medicine_category', 'medicine_name', 'quantity_needed', 'unit',
            'priority', 'description', 'patient_count', 'deadline',
            'latitude', 'longitude', 'location_name'
        ]
        widgets = {
            'medicine_category': forms.Select(attrs={'class': 'form-control'}),
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific medicine name'}),
            'quantity_needed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity needed'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., tablets, bottles'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the emergency situation'}),
            'patient_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of patients affected'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.0001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.0001'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location name'}),
        }

    def clean_medicine_name(self):
        medicine_name = self.cleaned_data.get('medicine_name')
        if medicine_name and len(medicine_name.strip()) < 2:
            raise forms.ValidationError("Medicine name must be at least 2 characters long.")
        return medicine_name

    def clean_quantity_needed(self):
        quantity_needed = self.cleaned_data.get('quantity_needed')
        if quantity_needed and quantity_needed <= 0:
            raise forms.ValidationError("Quantity must be a positive number.")
        if quantity_needed and quantity_needed > 999999:
            raise forms.ValidationError("Quantity cannot exceed 999,999.")
        return quantity_needed

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if unit and len(unit.strip()) < 1:
            raise forms.ValidationError("Unit cannot be empty.")
        if unit and len(unit) > 20:
            raise forms.ValidationError("Unit cannot exceed 20 characters.")
        return unit

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        if description and len(description) > 1000:
            raise forms.ValidationError("Description cannot exceed 1000 characters.")
        return description

    def clean_patient_count(self):
        patient_count = self.cleaned_data.get('patient_count')
        if patient_count and patient_count <= 0:
            raise forms.ValidationError("Patient count must be a positive number.")
        if patient_count and patient_count > 100000:
            raise forms.ValidationError("Patient count is unreasonably high.")
        return patient_count

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future.")
        return deadline

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude and (latitude < -90 or latitude > 90):
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude and (longitude < -180 or longitude > 180):
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def clean_location_name(self):
        location_name = self.cleaned_data.get('location_name')
        if location_name and len(location_name.strip()) < 2:
            raise forms.ValidationError("Location name must be at least 2 characters long.")
        return location_name


class BulkDonationRequestForm(forms.ModelForm):
    class Meta:
        model = BulkDonationRequest
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Request Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your bulk medicine needs'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        if title and len(title) > 100:
            raise forms.ValidationError("Title cannot exceed 100 characters.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        if description and len(description) > 1000:
            raise forms.ValidationError("Description cannot exceed 1000 characters.")
        return description


class BulkDonationItemForm(forms.ModelForm):
    class Meta:
        model = BulkDonationItem
        fields = ['medicine_category', 'medicine_name', 'quantity_requested', 'unit', 'urgency_level', 'notes']
        widgets = {
            'medicine_category': forms.Select(attrs={'class': 'form-control'}),
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific medicine name'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity needed'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., tablets, bottles'}),
            'urgency_level': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes'}),
        }

    def clean_medicine_name(self):
        medicine_name = self.cleaned_data.get('medicine_name')
        if medicine_name and len(medicine_name.strip()) < 2:
            raise forms.ValidationError("Medicine name must be at least 2 characters long.")
        return medicine_name

    def clean_quantity_requested(self):
        quantity_requested = self.cleaned_data.get('quantity_requested')
        if quantity_requested and quantity_requested <= 0:
            raise forms.ValidationError("Quantity must be a positive number.")
        if quantity_requested and quantity_requested > 999999:
            raise forms.ValidationError("Quantity cannot exceed 999,999.")
        return quantity_requested

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if unit and len(unit.strip()) < 1:
            raise forms.ValidationError("Unit cannot be empty.")
        if unit and len(unit) > 20:
            raise forms.ValidationError("Unit cannot exceed 20 characters.")
        return unit

    def clean_notes(self):
        notes = self.cleaned_data.get('notes')
        if notes and len(notes) > 500:
            raise forms.ValidationError("Notes cannot exceed 500 characters.")
        return notes


class MedicineVerificationForm(forms.ModelForm):
    class Meta:
        model = MedicineVerification
        fields = ['status', 'notes', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Verification notes'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for rejection'}),
        }

    def clean_notes(self):
        notes = self.cleaned_data.get('notes')
        if notes and len(notes) > 500:
            raise forms.ValidationError("Notes cannot exceed 500 characters.")
        return notes

    def clean_rejection_reason(self):
        rejection_reason = self.cleaned_data.get('rejection_reason')
        status = self.cleaned_data.get('status')
        
        if status == 'rejected' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting a medicine.")
        
        if rejection_reason and len(rejection_reason.strip()) < 5:
            raise forms.ValidationError("Rejection reason must be at least 5 characters long.")
        
        if rejection_reason and len(rejection_reason) > 500:
            raise forms.ValidationError("Rejection reason cannot exceed 500 characters.")
        
        return rejection_reason


class MedicineInventoryForm(forms.ModelForm):
    class Meta:
        model = MedicineInventory
        fields = ['medicine_category', 'medicine_name', 'current_stock', 'minimum_stock_level', 'unit', 'auto_reorder']
        widgets = {
            'medicine_category': forms.Select(attrs={'class': 'form-control'}),
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine name'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current stock level'}),
            'minimum_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum stock level'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit of measurement'}),
            'auto_reorder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_medicine_name(self):
        medicine_name = self.cleaned_data.get('medicine_name')
        if medicine_name and len(medicine_name.strip()) < 2:
            raise forms.ValidationError("Medicine name must be at least 2 characters long.")
        return medicine_name

    def clean_current_stock(self):
        current_stock = self.cleaned_data.get('current_stock')
        if current_stock is not None and current_stock < 0:
            raise forms.ValidationError("Current stock cannot be negative.")
        if current_stock and current_stock > 999999:
            raise forms.ValidationError("Current stock cannot exceed 999,999.")
        return current_stock

    def clean_minimum_stock_level(self):
        minimum_stock_level = self.cleaned_data.get('minimum_stock_level')
        if minimum_stock_level is not None and minimum_stock_level < 0:
            raise forms.ValidationError("Minimum stock level cannot be negative.")
        if minimum_stock_level and minimum_stock_level > 999999:
            raise forms.ValidationError("Minimum stock level cannot exceed 999,999.")
        return minimum_stock_level

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if unit and len(unit.strip()) < 1:
            raise forms.ValidationError("Unit cannot be empty.")
        if unit and len(unit) > 20:
            raise forms.ValidationError("Unit cannot exceed 20 characters.")
        return unit

    def clean(self):
        cleaned_data = super().clean()
        current_stock = cleaned_data.get('current_stock')
        minimum_stock_level = cleaned_data.get('minimum_stock_level')
        
        if current_stock is not None and minimum_stock_level is not None:
            if minimum_stock_level > current_stock:
                raise forms.ValidationError("Minimum stock level cannot be greater than current stock.")
        
        return cleaned_data


class AdvancedMedicineSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, brand, or generic name...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=MedicineCategory.objects.filter(active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Category'
    )
    prescription_required = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('yes', 'Prescription Required'), ('no', 'No Prescription')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Prescription'
    )
    condition = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')] + list(Medicine.CONDITION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Condition'
    )
    expiring_soon = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Expiring soon (within 30 days)'
    )
    rating_min = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '5', 'step': '0.5'}),
        label='Minimum Rating'
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
        label='Your Latitude'
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
        label='Your Longitude'
    )
    radius = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[
            (10, 'Within 10 km'),
            (25, 'Within 25 km'),
            (50, 'Within 50 km'),
            (100, 'Within 100 km'),
        ]),
        label='Search Radius',
        initial=50
    )

    def clean_query(self):
        query = self.cleaned_data.get('query')
        if query and len(query.strip()) > 100:
            raise forms.ValidationError("Search query cannot exceed 100 characters.")
        return query

    def clean_rating_min(self):
        rating_min = self.cleaned_data.get('rating_min')
        if rating_min is not None:
            if rating_min < 0 or rating_min > 5:
                raise forms.ValidationError("Minimum rating must be between 0 and 5.")
        return rating_min

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None:
            if latitude < -90 or latitude > 90:
                raise forms.ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None:
            if longitude < -180 or longitude > 180:
                raise forms.ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def clean_radius(self):
        radius = self.cleaned_data.get('radius')
        if radius is not None:
            if radius <= 0:
                raise forms.ValidationError("Radius must be a positive number.")
            if radius > 500:
                raise forms.ValidationError("Search radius cannot exceed 500 km.")
        return radius
