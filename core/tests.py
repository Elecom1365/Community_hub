from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.models import Donation, FundraisingCampaign, Membership, Organisation, Shift, ShiftBooking, Task, TaskAssignment, UrgentNeed

class PlatformWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.org = Organisation.objects.create(name="Test Community")
        self.admin = User.objects.create_user(username="admin-test", password="TestPass123!", is_staff=True)
        self.volunteer = User.objects.create_user(username="volunteer-test", password="TestPass123!")
        self.admin_membership = Membership.objects.get(user=self.admin, organisation=self.org)
        self.admin_membership.role = Membership.Role.ADMIN
        self.admin_membership.save()
        self.volunteer_membership = Membership.objects.get(user=self.volunteer, organisation=self.org)
        self.client.force_login(self.admin)

    def test_admin_dashboard_loads(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good to see you")

    def test_admin_can_record_donation(self):
        response = self.client.post(reverse("donations"), {
            "donation_type": "financial", "donor_name": "Test Donor", "donor_email": "donor@example.test",
            "amount": "25.00", "currency": "GBP", "item_description": "", "quantity": "1",
            "received_at": timezone.localdate().isoformat(), "campaign": "", "notes": "Test record"
        })
        self.assertRedirects(response, reverse("donations"))
        self.assertTrue(Donation.objects.filter(organisation=self.org, donor_name="Test Donor", amount=Decimal("25.00")).exists())

    def test_volunteer_cannot_access_donation_management(self):
        self.client.force_login(self.volunteer)
        response = self.client.get(reverse("donations"))
        self.assertEqual(response.status_code, 403)

    def test_volunteer_can_book_open_shift(self):
        shift = Shift.objects.create(organisation=self.org, created_by=self.admin_membership, title="Test shift", start_time=timezone.now() + timedelta(days=1), end_time=timezone.now() + timedelta(days=1, hours=2), capacity=1)
        self.client.force_login(self.volunteer)
        response = self.client.post(reverse("book_shift", args=[shift.id]))
        self.assertRedirects(response, reverse("shifts"))
        self.assertTrue(ShiftBooking.objects.filter(shift=shift, volunteer_membership=self.volunteer_membership, status=ShiftBooking.Status.BOOKED).exists())

    def test_volunteer_cannot_book_shift_from_another_organisation(self):
        other_org = Organisation.objects.create(name="Other Organisation")
        shift = Shift.objects.create(organisation=other_org, created_by=self.admin_membership, title="Outside shift", start_time=timezone.now() + timedelta(days=1), end_time=timezone.now() + timedelta(days=1, hours=2), capacity=1)
        self.client.force_login(self.volunteer)
        response = self.client.post(reverse("book_shift", args=[shift.id]))
        self.assertEqual(response.status_code, 404)
