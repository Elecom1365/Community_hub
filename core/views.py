import csv
from decimal import Decimal
from io import BytesIO
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.db import transaction
from django.db.models import Sum, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from core.forms import SignupForm, DonationForm, CampaignForm, ShiftForm, TaskForm, NeedForm, VolunteerProfileForm, AssignTaskForm
from core.models import Donation, DonationReceipt, FundraisingCampaign, Membership, Organisation, Shift, ShiftBooking, Task, TaskAssignment, UrgentNeed, VolunteerProfile

def current_membership(user):
    return Membership.objects.filter(user=user, is_active=True).select_related("organisation").first()

def admin_required(view_func):
    def wrapped(request, *args, **kwargs):
        membership = current_membership(request.user)
        if not membership or membership.role != Membership.Role.ADMIN:
            return HttpResponseForbidden("You do not have permission to access this page.")
        request.membership = membership
        request.organisation = membership.organisation
        return view_func(request, *args, **kwargs)
    return login_required(wrapped)

def member_required(view_func):
    def wrapped(request, *args, **kwargs):
        membership = current_membership(request.user)
        if not membership:
            return HttpResponseForbidden("Your account is not linked to an active organisation.")
        request.membership = membership
        request.organisation = membership.organisation
        return view_func(request, *args, **kwargs)
    return login_required(wrapped)

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/landing.html")

def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your volunteer account has been created.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Create volunteer account", "submit_label": "Create account"})

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "core/login.html", {"form": form})

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("dashboard")

@member_required
def dashboard(request):
    org = request.organisation
    membership = request.membership
    donations = Donation.objects.filter(organisation=org)
    if membership.role != Membership.Role.ADMIN:
        donations = donations.none()
    context = {
        "membership": membership,
        "donation_total": donations.filter(donation_type=Donation.Type.FINANCIAL).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "donation_count": donations.count(),
        "volunteer_count": Membership.objects.filter(organisation=org, role=Membership.Role.VOLUNTEER, is_active=True).count(),
        "open_shifts": Shift.objects.filter(organisation=org, status=Shift.Status.OPEN, start_time__gte=timezone.now()).count(),
        "open_tasks": Task.objects.filter(organisation=org).exclude(status=Task.Status.COMPLETED).count() if membership.role == Membership.Role.ADMIN else TaskAssignment.objects.filter(membership=membership).exclude(status=TaskAssignment.Status.COMPLETED).count(),
        "open_needs": UrgentNeed.objects.filter(organisation=org).exclude(status__in=[UrgentNeed.Status.FULFILLED, UrgentNeed.Status.CLOSED]).count(),
        "campaigns": FundraisingCampaign.objects.filter(organisation=org).order_by("-created_at")[:5],
        "recent_donations": donations.order_by("-created_at")[:5],
    }
    return render(request, "core/dashboard.html", context)

@admin_required
def donations(request):
    qs = Donation.objects.filter(organisation=request.organisation).select_related("recorded_by__user", "campaign").order_by("-received_at", "-id")
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(donor_name__icontains=query)
    form = DonationForm(request.POST or None, organisation=request.organisation)
    if request.method == "POST" and form.is_valid():
        donation = form.save(commit=False)
        donation.organisation = request.organisation
        donation.recorded_by = request.membership
        if donation.campaign and donation.campaign.organisation_id != request.organisation.id:
            form.add_error("campaign", "Select a campaign from your organisation.")
        else:
            donation.save()
            messages.success(request, "Donation recorded successfully.")
            return redirect("donations")
    return render(request, "core/donations.html", {"donations": qs, "form": form, "query": query})

@admin_required
def receipt_pdf(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id, organisation=request.organisation)
    receipt, created = DonationReceipt.objects.get_or_create(donation=donation, defaults={"receipt_number": f"CH-{timezone.now():%Y%m%d}-{donation.id:06d}"})
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle(f"Donation receipt {receipt.receipt_number}")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(55, height - 70, request.organisation.name)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(55, height - 115, "Donation receipt")
    pdf.setFont("Helvetica", 11)
    rows = [f"Receipt number: {receipt.receipt_number}", f"Donor: {donation.donor_name}", f"Date received: {donation.received_at:%d %B %Y}", f"Donation type: {donation.get_donation_type_display()}"]
    if donation.donation_type == Donation.Type.FINANCIAL:
        rows.append(f"Amount: {donation.currency} {donation.amount:,.2f}")
    else:
        rows.extend([f"Items: {donation.item_description}", f"Quantity: {donation.quantity}"])
    if donation.campaign:
        rows.append(f"Campaign: {donation.campaign.title}")
    y = height - 155
    for row in rows:
        pdf.drawString(55, y, row[:110])
        y -= 25
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(55, 70, "This document confirms that the donation has been recorded by the organisation.")
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{receipt.receipt_number}.pdf"'
    return response


@admin_required
def campaigns(request):
    qs = FundraisingCampaign.objects.filter(
        organisation=request.organisation
    ).annotate(
        raised=Sum("donations__amount")
    ).order_by("-created_at")

    form = CampaignForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.organisation = request.organisation
        campaign.managed_by = request.membership
        campaign.save()
        messages.success(request, "Fundraising campaign created.")
        return redirect("campaigns")

    return render(
        request,
        "core/campaigns.html",
        {"campaigns": qs, "form": form}
    )


@admin_required
@require_POST
def update_campaign_status(request, campaign_id):
    campaign = get_object_or_404(
        FundraisingCampaign,
        id=campaign_id,
        organisation=request.organisation
    )

    status = request.POST.get("status")
    valid_statuses = [choice[0] for choice in FundraisingCampaign.Status.choices]

    if status not in valid_statuses:
        messages.error(request, "Please select a valid campaign status.")
        return redirect("campaigns")

    campaign.status = status
    campaign.save(update_fields=["status"])
    messages.success(request, f"Campaign status updated to {campaign.get_status_display()}.")
    return redirect("campaigns")


@member_required
def shifts(request):
    qs = Shift.objects.filter(organisation=request.organisation).prefetch_related("bookings__volunteer_membership__user").order_by("start_time")
    form = ShiftForm(request.POST or None)
    if request.membership.role == Membership.Role.ADMIN and request.method == "POST" and form.is_valid():
        shift = form.save(commit=False)
        shift.organisation = request.organisation
        shift.created_by = request.membership
        shift.save()
        messages.success(request, "Volunteer shift created.")
        return redirect("shifts")
    return render(request, "core/shifts.html", {"shifts": qs, "form": form, "is_admin": request.membership.role == Membership.Role.ADMIN, "now": timezone.now()})

@member_required
@require_POST
def book_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id, organisation=request.organisation)
    if request.membership.role != Membership.Role.VOLUNTEER:
        messages.error(request, "Only volunteer accounts can book shifts.")
        return redirect("shifts")
    if shift.status != Shift.Status.OPEN or shift.start_time <= timezone.now():
        messages.error(request, "This shift is not available for booking.")
        return redirect("shifts")
    with transaction.atomic():
        locked_shift = Shift.objects.select_for_update().get(pk=shift.pk)
        existing = ShiftBooking.objects.filter(shift=locked_shift, volunteer_membership=request.membership).first()
        if existing and existing.status == ShiftBooking.Status.BOOKED:
            messages.info(request, "You already have a booking for this shift.")
        elif locked_shift.active_booking_count >= locked_shift.capacity:
            messages.error(request, "This shift is full.")
        elif existing:
            existing.status = ShiftBooking.Status.BOOKED
            existing.save(update_fields=["status"])
            messages.success(request, "Your shift booking is active again.")
        else:
            ShiftBooking.objects.create(shift=locked_shift, volunteer_membership=request.membership)
            messages.success(request, "Your shift has been booked.")
    return redirect("shifts")

@member_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(ShiftBooking, id=booking_id, shift__organisation=request.organisation)
    if request.membership.role != Membership.Role.ADMIN and booking.volunteer_membership_id != request.membership.id:
        return HttpResponseForbidden("You cannot change another volunteer's booking.")
    if booking.status == ShiftBooking.Status.BOOKED:
        booking.status = ShiftBooking.Status.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "Booking cancelled.")
    return redirect("shifts")

@member_required
def tasks(request):
    form = TaskForm(request.POST or None)
    if request.membership.role == Membership.Role.ADMIN:
        qs = Task.objects.filter(organisation=request.organisation).select_related("created_by__user").order_by("status", "due_date")
        if request.method == "POST" and form.is_valid():
            task = form.save(commit=False)
            task.organisation = request.organisation
            task.created_by = request.membership
            task.save()
            messages.success(request, "Task created.")
            return redirect("tasks")
    else:
        qs = Task.objects.filter(assignments__membership=request.membership).distinct().order_by("status", "due_date")
    return render(request, "core/tasks.html", {"tasks": qs, "form": form, "is_admin": request.membership.role == Membership.Role.ADMIN})

@admin_required
def assign_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, organisation=request.organisation)
    form = AssignTaskForm(request.POST or None, organisation=request.organisation)
    if request.method == "POST" and form.is_valid():
        membership = form.cleaned_data["membership"]
        TaskAssignment.objects.get_or_create(task=task, membership=membership)
        messages.success(request, "Task assigned.")
        return redirect("tasks")
    return render(request, "core/form_page.html", {"form": form, "title": f"Assign: {task.title}", "submit_label": "Assign task"})

@member_required
@require_POST
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, organisation=request.organisation)
    status = request.POST.get("status")
    if request.membership.role == Membership.Role.ADMIN:
        if status in Task.Status.values:
            task.status = status
            task.save(update_fields=["status"])
    else:
        assignment = get_object_or_404(TaskAssignment, task=task, membership=request.membership)
        if status in TaskAssignment.Status.values:
            assignment.status = status
            assignment.save(update_fields=["status"])
            if status == TaskAssignment.Status.COMPLETED:
                task.status = Task.Status.COMPLETED
                task.save(update_fields=["status"])
    messages.success(request, "Task status updated.")
    return redirect("tasks")

@member_required
def needs(request):
    qs = UrgentNeed.objects.filter(organisation=request.organisation).order_by("status", "needed_by")
    form = NeedForm(request.POST or None)
    if request.membership.role == Membership.Role.ADMIN and request.method == "POST" and form.is_valid():
        need = form.save(commit=False)
        need.organisation = request.organisation
        need.created_by = request.membership
        need.save()
        messages.success(request, "Urgent resource need published.")
        return redirect("needs")
    return render(request, "core/needs.html", {"needs": qs, "form": form, "is_admin": request.membership.role == Membership.Role.ADMIN})

@admin_required
def reports(request):
    org = request.organisation
    donations = Donation.objects.filter(organisation=org)
    financial_total = donations.filter(donation_type=Donation.Type.FINANCIAL).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    campaign_rows = FundraisingCampaign.objects.filter(organisation=org).annotate(raised=Sum("donations__amount")).order_by("title")
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="nonprofit-report.csv"'
        writer = csv.writer(response)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Financial donations total (GBP equivalent not converted)", str(financial_total)])
        writer.writerow(["Donation records", donations.count()])
        writer.writerow(["Active volunteers", Membership.objects.filter(organisation=org, role=Membership.Role.VOLUNTEER, is_active=True).count()])
        writer.writerow(["Shifts", Shift.objects.filter(organisation=org).count()])
        writer.writerow(["Tasks", Task.objects.filter(organisation=org).count()])
        for campaign in campaign_rows:
            writer.writerow([f"Campaign: {campaign.title}", str(campaign.raised or Decimal("0.00"))])
        return response
    return render(request, "core/reports.html", {"financial_total": financial_total, "donation_count": donations.count(), "volunteer_count": Membership.objects.filter(organisation=org, role=Membership.Role.VOLUNTEER, is_active=True).count(), "shift_count": Shift.objects.filter(organisation=org).count(), "task_count": Task.objects.filter(organisation=org).count(), "campaigns": campaign_rows})

@member_required
def profile(request):
    membership = request.membership
    volunteer_profile, _ = VolunteerProfile.objects.get_or_create(membership=membership)
    form = VolunteerProfileForm(request.POST or None, instance=volunteer_profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    return render(request, "core/form_page.html", {"form": form, "title": "My volunteer profile", "submit_label": "Save profile"})

@admin_required
def members(request):
    qs = Membership.objects.filter(organisation=request.organisation).select_related("user").order_by("role", "user__username")
    return render(request, "core/members.html", {"members": qs})

@admin_required
@require_POST
def change_member_role(request, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, organisation=request.organisation)
    role = request.POST.get("role")
    if membership.user_id == request.user.id:
        messages.error(request, "You cannot change your own role here.")
    elif role in Membership.Role.values:
        membership.role = role
        membership.save(update_fields=["role"])
        if role == Membership.Role.VOLUNTEER:
            VolunteerProfile.objects.get_or_create(membership=membership)
        messages.success(request, "Member role updated.")
    return redirect("members")
