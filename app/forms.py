from django import forms
from django.contrib.auth.models import User
from datetime import date
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
            'name', 'brand_name', 'generic_name', 'category', 'subcategory',
            'description', 'dosage_form', 'strength', 'composition', 'quantity', 'unit',
            'condition', 'expiry_date', 'manufacture_date', 'batch_number', 'manufacturer',
            'storage_condition', 'usage_instructions', 'side_effects', 'contraindications',
            'prescription_required', 'pickup_available', 'delivery_available',
            'latitude', 'longitude', 'location_name', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine Name'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name (e.g., Tylenol)'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Generic Name (e.g., Paracetamol)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed Description'}),
            'dosage_form': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select Dosage Form'),
                ('Tablet', 'Tablet'),
                ('Capsule', 'Capsule'),
                ('Syrup', 'Syrup'),
                ('Injection', 'Injection'),
                ('Cream', 'Cream/Ointment'),
                ('Drops', 'Drops'),
                ('Other', 'Other'),
            ]),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg, 10ml'}),
            'composition': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Active ingredients'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., tablets, bottles, vials'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': date.today().isoformat()}),
            'manufacture_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': date.today().isoformat()}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch/Lot Number'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manufacturer Name'}),
            'storage_condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Room temperature, Refrigerate'}),
            'usage_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'How to use'}),
            'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Common side effects'}),
            'contraindications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'When not to use'}),
            'prescription_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pickup_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'delivery_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < date.today():
            raise forms.ValidationError("Expiry date must be today or in the future.")
        return expiry_date

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        if subcategory and category and subcategory.category != category:
            raise forms.ValidationError("Selected subcategory does not belong to the selected category.")
        return cleaned_data


class UserSignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )
    role = forms.ChoiceField(
        choices=[('donor', 'Medicine Donor'), ('ngo', 'NGO/Hospital'), ('delivery_boy', 'Delivery Boy')],
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

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")

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


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['quantity_requested', 'message']
        widgets = {
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity Needed'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Message to Donor'}),
        }


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


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'})
    )


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}),
        label='New Password'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")

        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long!")

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


class BulkDonationRequestForm(forms.ModelForm):
    class Meta:
        model = BulkDonationRequest
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Request Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your bulk medicine needs'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }


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


class MedicineVerificationForm(forms.ModelForm):
    class Meta:
        model = MedicineVerification
        fields = ['status', 'notes', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Verification notes'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for rejection'}),
        }


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
