from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Donation, FundraisingCampaign, Membership, Organisation, Shift, Task, TaskAssignment, UrgentNeed, VolunteerProfile

class Command(BaseCommand):
    help = "Create synthetic demonstration data for the local project."

    def handle(self, *args, **options):
        User = get_user_model()
        org, _ = Organisation.objects.get_or_create(name="Community Support Organisation")
        admin, _ = User.objects.get_or_create(username="demo-admin", defaults={"email": "admin@example.test", "first_name": "Alex", "last_name": "Morgan", "is_staff": True})
        admin.set_password("ChangeMe123!")
        admin.is_staff = True
        admin.save()
        volunteer, _ = User.objects.get_or_create(username="demo-volunteer", defaults={"email": "volunteer@example.test", "first_name": "Sam", "last_name": "Taylor"})
        volunteer.set_password("ChangeMe123!")
        volunteer.save()
        admin_membership, _ = Membership.objects.update_or_create(organisation=org, user=admin, defaults={"role": Membership.Role.ADMIN, "is_active": True})
        volunteer_membership, _ = Membership.objects.update_or_create(organisation=org, user=volunteer, defaults={"role": Membership.Role.VOLUNTEER, "is_active": True})
        VolunteerProfile.objects.get_or_create(membership=volunteer_membership, defaults={"skills": "Event support, packing donations", "availability_notes": "Weekends"})
        campaign, _ = FundraisingCampaign.objects.get_or_create(organisation=org, title="Winter Essentials", defaults={"managed_by": admin_membership, "description": "Help local households access essential supplies.", "target_amount": Decimal("2500.00"), "currency": "GBP", "start_date": timezone.localdate(), "end_date": timezone.localdate() + timedelta(days=45), "status": FundraisingCampaign.Status.ACTIVE})
        Donation.objects.get_or_create(organisation=org, donor_name="Example Community Donor", received_at=timezone.localdate(), donation_type=Donation.Type.FINANCIAL, defaults={"recorded_by": admin_membership, "campaign": campaign, "donor_email": "donor@example.test", "amount": Decimal("75.00"), "currency": "GBP", "quantity": 1})
        Donation.objects.get_or_create(organisation=org, donor_name="Local Supplies Group", received_at=timezone.localdate(), donation_type=Donation.Type.IN_KIND, defaults={"recorded_by": admin_membership, "item_description": "Warm blankets", "quantity": 12, "amount": Decimal("0.00"), "currency": "GBP"})
        Shift.objects.get_or_create(organisation=org, title="Community pantry support", defaults={"created_by": admin_membership, "description": "Help organise and distribute donated food and essentials.", "start_time": timezone.now() + timedelta(days=2), "end_time": timezone.now() + timedelta(days=2, hours=3), "capacity": 6, "status": Shift.Status.OPEN})
        task, _ = Task.objects.get_or_create(organisation=org, title="Prepare donation collection area", defaults={"created_by": admin_membership, "description": "Organise labelled boxes before the next collection.", "priority": Task.Priority.MEDIUM, "status": Task.Status.OPEN, "due_date": timezone.localdate() + timedelta(days=4)})
        TaskAssignment.objects.get_or_create(task=task, membership=volunteer_membership)
        UrgentNeed.objects.get_or_create(organisation=org, title="Warm blankets", defaults={"created_by": admin_membership, "description": "Blankets for households during colder weather.", "resource_type": "Blankets", "quantity_needed": 25, "status": UrgentNeed.Status.OPEN, "needed_by": timezone.localdate() + timedelta(days=7)})
        self.stdout.write(self.style.SUCCESS("Demo data created or refreshed."))
        self.stdout.write("Administrator: demo-admin / ChangeMe123!")
        self.stdout.write("Volunteer: demo-volunteer / ChangeMe123!")
        self.stdout.write("Change these passwords before any deployment and do not use the demo accounts for real personal data.")
