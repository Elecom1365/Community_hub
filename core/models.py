from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

class Organisation(models.Model):
    name = models.CharField(max_length=180, default="Community Support Organisation")
    registration_number = models.CharField(max_length=80, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        VOLUNTEER = "volunteer", "Volunteer"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VOLUNTEER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organisation", "user"], name="unique_org_membership")]

    def __str__(self):
        return f"{self.user} - {self.organisation}"

class VolunteerProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="volunteer_profile")
    phone = models.CharField(max_length=40, blank=True)
    skills = models.TextField(blank=True)
    availability_notes = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=180, blank=True)

    def __str__(self):
        return f"Profile for {self.membership.user}"

class FundraisingCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="campaigns")
    managed_by = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="managed_campaigns")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=3, default="GBP")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Donation(models.Model):
    class Type(models.TextChoices):
        FINANCIAL = "financial", "Financial"
        IN_KIND = "in_kind", "In-kind"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="donations")
    recorded_by = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="recorded_donations")
    campaign = models.ForeignKey(FundraisingCampaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="donations")
    donation_type = models.CharField(max_length=20, choices=Type.choices)
    donor_name = models.CharField(max_length=180)
    donor_email = models.EmailField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=3, default="GBP")
    item_description = models.CharField(max_length=250, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    received_at = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor_name} - {self.get_donation_type_display()}"

class DonationReceipt(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name="receipts")
    receipt_number = models.CharField(max_length=40, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number

class Shift(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="shifts")
    created_by = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="created_shifts")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def active_booking_count(self):
        return self.bookings.filter(status=ShiftBooking.Status.BOOKED).count()

    @property
    def available_places(self):
        return max(self.capacity - self.active_booking_count, 0)

class ShiftBooking(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
        ATTENDED = "attended", "Attended"
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="bookings")
    volunteer_membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="shift_bookings")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["shift", "volunteer_membership"], name="unique_shift_membership_booking")]

class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="tasks")
    created_by = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="created_tasks")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TaskAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="assignments")
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="task_assignments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["task", "membership"], name="unique_task_membership_assignment")]

class UrgentNeed(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIALLY_FULFILLED = "partially_fulfilled", "Partially fulfilled"
        FULFILLED = "fulfilled", "Fulfilled"
        CLOSED = "closed", "Closed"
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="urgent_needs")
    created_by = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name="created_needs")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=120)
    quantity_needed = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)
    needed_by = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
