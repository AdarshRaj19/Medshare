from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class MedicineCategory(models.Model):
    """Medicine categories for better organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome icon class
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Medicine Categories"

    def __str__(self):
        return self.name


class MedicineSubcategory(models.Model):
    """Subcategories within medicine categories"""
    category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('category', 'name')
        verbose_name_plural = "Medicine Subcategories"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('ngo', 'NGO'),
        ('admin', 'Admin')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='donor')
    phone = models.CharField(max_length=20, blank=True, null=True)
    organization_name = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    verified = models.BooleanField(default=False)
    license_number = models.CharField(max_length=100, blank=True, null=True)  # For NGOs
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)
    location_confidence = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Confidence of location: 'high', 'low', or 'unknown'."
    )
    preferred_contact_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'), ('phone', 'Phone'), ('both', 'Both')
    ], default='email')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class MedicineQuerySet(models.QuerySet):
    """Custom QuerySet to filter out expired medicines by default"""
    def available_only(self):
        """Return only non-expired medicines"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.exclude(status='expired').filter(expiry_date__gte=today)


class MedicineManager(models.Manager):
    """Custom manager for Medicine model"""
    def get_queryset(self):
        return MedicineQuerySet(self.model, using=self._db)
    
    def available_only(self):
        """Return only non-expired, available medicines"""
        return self.get_queryset().available_only()


class Medicine(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('requested', 'Requested'),
        ('donated', 'Donated'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('quality_check', 'Quality Check'),
        ('distributed', 'Distributed')
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New/Sealed'),
        ('opened', 'Opened but Unused'),
        ('partial', 'Partially Used'),
        ('unknown', 'Unknown')
    ]
    
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    category = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    subcategory = models.ForeignKey(MedicineSubcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    brand_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    composition = models.TextField(blank=True, null=True)  # Active ingredients
    dosage_form = models.CharField(max_length=50, blank=True, null=True)  # Tablet, Syrup, Injection, etc.
    strength = models.CharField(max_length=50, blank=True, null=True)  # 500mg, 10ml, etc.
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit = models.CharField(max_length=20, default='units')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    expiry_date = models.DateField()
    manufacture_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    storage_condition = models.CharField(max_length=100, blank=True, null=True)
    usage_instructions = models.TextField(blank=True, null=True)
    side_effects = models.TextField(blank=True, null=True)
    contraindications = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True, null=True)
    location_confidence = models.CharField(max_length=20, blank=True, null=True, help_text="Confidence of location: 'high', 'low', or 'unknown'.")
    pickup_available = models.BooleanField(default=True)
    delivery_available = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='medicines/', null=True, blank=True)
    prescription_required = models.BooleanField(default=False)
    verified_by_admin = models.BooleanField(default=False)
    
    # AI/Recommendation fields
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_count = models.IntegerField(default=0)
    recommendation_score = models.FloatField(default=0)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    viewed_by = models.ManyToManyField(User, related_name='viewed_medicines', blank=True)
    
    # Custom manager
    objects = MedicineManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    def days_until_expiry(self):
        from datetime import date
        return (self.expiry_date - date.today()).days

    def is_expiring_soon(self):
        return 0 <= self.days_until_expiry() <= 30

    def is_expired(self):
        from datetime import date
        return self.expiry_date < date.today()

    def get_display_name(self):
        """Return formatted medicine name with brand and generic"""
        if self.brand_name and self.generic_name:
            return f"{self.brand_name} ({self.generic_name})"
        elif self.brand_name:
            return self.brand_name
        else:
            return self.name

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
    
    def days_until_expiry(self):
        from datetime import date
        return (self.expiry_date - date.today()).days
    
    def is_expiring_soon(self):
        return 0 <= self.days_until_expiry() <= 30
    
    def is_expired(self):
        from datetime import date
        return self.expiry_date < date.today()
    
    def mark_expired_if_needed(self):
        """Auto-mark medicine as expired if expiry date has passed"""
        if self.is_expired() and self.status != 'expired':
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def find_duplicates(self):
        """Find medicines with same name + expiry date by same donor (exclude self)"""
        duplicates = Medicine.objects.filter(
            donor=self.donor,
            name=self.name,
            expiry_date=self.expiry_date,
            status='available'
        ).exclude(id=self.id)
        return duplicates
    
    def merge_with_duplicate(self, other_medicine):
        """Merge another medicine into this one (sum quantities)"""
        if other_medicine.donor != self.donor or other_medicine.name != self.name:
            raise ValueError("Can only merge medicines from same donor with same name")
        
        self.quantity += other_medicine.quantity
        self.save(update_fields=['quantity', 'updated_at'])
        other_medicine.delete()
        return self


class MedicineRating(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('medicine', 'user')

    def __str__(self):
        return f"{self.medicine.name} - {self.rating}/5"


class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicine_requests', null=True, blank=True)
    requester_type = models.CharField(max_length=20, choices=[('ngo', 'NGO'), ('individual', 'Individual')], default='individual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    quantity_requested = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

# PickupDelivery workflow model
class PickupDelivery(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("picked_up", "Picked Up"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("unable_to_pickup", "Unable to Pickup"),
    ]
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="deliveries")
    donation_request = models.OneToOneField(DonationRequest, on_delete=models.CASCADE, related_name="pickup_delivery")
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ngo_deliveries")
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="donor_deliveries")
    delivery_boy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_deliveries")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    preferred_delivery_datetime = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    unable_to_pickup_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Delivery for {self.medicine.name} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.username} requested {self.medicine.name}"


class MedicineSearchLog(models.Model):
    """AI: Track search patterns for recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    search_query = models.CharField(max_length=200)
    medicine_results = models.ManyToManyField(Medicine, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Search: {self.search_query}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    donation_request = models.ForeignKey(DonationRequest, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ContactMessage(models.Model):
    """Contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Testimonial(models.Model):
    """User testimonials and success stories"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials', null=True, blank=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=[('donor', 'Medicine Donor'), ('ngo', 'NGO/Hospital')])
    message = models.TextField()
    image = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.role}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('donation', 'How to Donate'),
        ('request', 'How to Request'),
        ('safety', 'Safety & Guidelines'),
        ('technical', 'Technical Support'),
        ('other', 'Other')
    ])
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class MedicineVerification(models.Model):
    """Quality verification for medicines"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_info', 'More Info Required')
    ]
    
    medicine = models.OneToOneField(Medicine, on_delete=models.CASCADE, related_name='verification')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verification for {self.medicine.name}"


class EmergencyAlert(models.Model):
    """Emergency medicine requests"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_alerts')
    medicine_category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=100)
    quantity_needed = models.IntegerField(validators=[MinValueValidator(1)])
    unit = models.CharField(max_length=20, default='units')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    description = models.TextField()
    patient_count = models.IntegerField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"Emergency: {self.medicine_name} - {self.ngo.username}"


class EmergencyAlertResponse(models.Model):
    alert = models.ForeignKey('EmergencyAlert', on_delete=models.CASCADE, related_name='responses')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_responses')
    quantity_offered = models.IntegerField(validators=[MinValueValidator(1)])
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('alert', 'donor')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.donor.username} response to {self.alert.medicine_name}"


class AuditLog(models.Model):
    """Audit trail for all important actions"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('donate', 'Donate'),
        ('request', 'Request'),
        ('login', 'Login'),
        ('logout', 'Logout')
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    changes = models.JSONField(null=True, blank=True)  # Store what changed
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action} - {self.model_name}"


class BulkDonationRequest(models.Model):
    """NGOs can request multiple medicines at once"""
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_requests')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('partial', 'Partially Fulfilled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk Request: {self.title} - {self.ngo.username}"


class BulkDonationItem(models.Model):
    """Individual items in a bulk donation request"""
    bulk_request = models.ForeignKey(BulkDonationRequest, on_delete=models.CASCADE, related_name='items')
    medicine_category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=100)
    quantity_requested = models.IntegerField(validators=[MinValueValidator(1)])
    unit = models.CharField(max_length=20, default='units')
    urgency_level = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    notes = models.TextField(blank=True, null=True)
    fulfilled_quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('partial', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled')
    ], default='pending')

    def __str__(self):
        return f"{self.medicine_name} ({self.quantity_requested} {self.unit})"

    @property
    def remaining_quantity(self):
        return max(0, self.quantity_requested - self.fulfilled_quantity)


class PasswordResetToken(models.Model):
    """Password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.username}"


class PickupDelivery(models.Model):
    """Track pickup and delivery of medicines from donor to NGO/Hospital"""
    STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('unable_to_pickup', 'Unable to Pickup'),
        ('cancelled', 'Cancelled')
    ]
    
    donation_request = models.OneToOneField(DonationRequest, on_delete=models.CASCADE, related_name='pickup_delivery')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickups_given')
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickups_received')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='pickups')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pickup details
    scheduled_pickup_date = models.DateTimeField(null=True, blank=True)
    pickup_date = models.DateTimeField(null=True, blank=True)
    pickup_notes = models.TextField(blank=True, null=True)
    
    # Delivery details
    delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True, null=True)
    
    # Quantities
    quantity_scheduled = models.IntegerField()
    quantity_picked_up = models.IntegerField(null=True, blank=True, default=0)
    quantity_delivered = models.IntegerField(null=True, blank=True, default=0)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pickup/Delivery - {self.medicine.name} ({self.status})"
    
    def days_since_created(self):
        from datetime import date
        return (date.today() - self.created_at.date()).days


# Internal delivery models (DeliveryBoy, Delivery, DeliveryLocation) removed — platform now uses external Porter partners.


class PorterPartner(models.Model):
    """
    External porter/delivery partner information.
    Platform stores partner contact and optional tracking URL template.
    """
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True, null=True)
    external_tracking_url = models.URLField(blank=True, null=True, help_text="Optional partner tracking URL or template")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class DeliveryRequest(models.Model):
    """Delivery request routed to external porter partners (platform-coordination model)."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Partner'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    pickup_delivery = models.OneToOneField(PickupDelivery, on_delete=models.CASCADE, related_name='delivery_request')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_requests')
    porter_partner = models.ForeignKey(PorterPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')

    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    drop_latitude = models.FloatField(null=True, blank=True)
    drop_longitude = models.FloatField(null=True, blank=True)

    external_tracking_link = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DeliveryRequest #{self.id} - {self.get_status_display()}"
 
class MedicineInventory(models.Model):
    """NGO inventory for medicines"""
    medicine_name = models.CharField(max_length=100)
    current_stock = models.IntegerField(default=0)
    minimum_stock_level = models.IntegerField(default=0)
    unit = models.CharField(default='units', max_length=20)
    last_updated = models.DateTimeField(auto_now=True)
    auto_reorder = models.BooleanField(default=False)
    medicine_category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')

    class Meta:
        unique_together = (('ngo', 'medicine_category', 'medicine_name'),)

    def __str__(self):
        return f"{self.medicine_name} - {self.ngo.username} ({self.current_stock})"
 
class Conversation(models.Model):
    """Conversation between donor and NGO about a medicine"""
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donor_conversations')
    ngo = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ngo_conversations')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = (('medicine', 'donor', 'ngo'),)

    def __str__(self):
        return f"Conversation: {self.medicine.name} ({self.donor.username} -> {self.ngo.username})"
    
    def get_other_user(self, current_user):
        """Get the other user in the conversation"""
        if current_user == self.donor:
            return self.ngo
        elif current_user == self.ngo:
            return self.donor
        return None
    
    def get_other_user_role(self, current_user):
        """Get the role of the other user in the conversation"""
        other_user = self.get_other_user(current_user)
        if other_user:
            return getattr(other_user.profile, 'role', 'unknown')
        return None


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('location', 'Location'),
        ('location_request', 'Location Request'),
    ]
    
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    is_read = models.BooleanField(default=False)
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def get_distance_to(self, latitude, longitude):
        """Calculate distance in km using Haversine formula"""
        if not self.location_latitude or not self.location_longitude:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = radians(self.location_latitude), radians(self.location_longitude)
        lat2, lon2 = radians(latitude), radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return round(c * r, 2)


class ChatMessage(models.Model):
    """Store chatbot conversation history for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()  # User's question
    response = models.TextField()  # LLM's response
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True)  # Context medicine
    created_at = models.DateTimeField(auto_now_add=True)
    helpful = models.BooleanField(null=True, blank=True)  # User feedback (True/False/None)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['medicine']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}..."

class MedicineReport(models.Model):
    """Monthly/quarterly medicine donation reports"""
    REPORT_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual')
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)  # For monthly reports
    quarter = models.IntegerField(null=True, blank=True)  # For quarterly reports
    
    # Statistics
    total_medicines_donated = models.IntegerField(default=0)
    total_donors = models.IntegerField(default=0)
    total_ngos = models.IntegerField(default=0)
    total_requests_fulfilled = models.IntegerField(default=0)
    medicines_by_category = models.JSONField(default=dict)
    top_donors = models.JSONField(default=list)
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    def get_distance_to(self, latitude, longitude):
        """Calculate distance in km using Haversine formula"""
        if not self.location_latitude or not self.location_longitude:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = radians(self.location_latitude), radians(self.location_longitude)
        lat2, lon2 = radians(latitude), radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return round(c * r, 2)

