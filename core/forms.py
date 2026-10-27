from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from core.models import Donation, FundraisingCampaign, Membership, Shift, Task, TaskAssignment, UrgentNeed, VolunteerProfile

class SignupForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"

class DonationForm(StyledModelForm):
    class Meta:
        model = Donation
        fields = ["donation_type", "donor_name", "donor_email", "amount", "currency", "item_description", "quantity", "received_at", "campaign", "notes"]
        widgets = {"received_at": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}
    def __init__(self, *args, **kwargs):
        organisation = kwargs.pop("organisation", None)
        super().__init__(*args, **kwargs)
        if organisation:
            self.fields["campaign"].queryset = FundraisingCampaign.objects.filter(organisation=organisation)
        self.fields["campaign"].required = False

class CampaignForm(StyledModelForm):
    class Meta:
        model = FundraisingCampaign
        fields = ["title", "description", "target_amount", "currency", "start_date", "end_date", "status"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 3})}

class ShiftForm(StyledModelForm):
    class Meta:
        model = Shift
        fields = ["title", "description", "start_time", "end_time", "capacity", "status"]
        widgets = {"start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}), "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}), "description": forms.Textarea(attrs={"rows": 3})}
    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "End time must be later than start time.")
        return cleaned

class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "status", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 3})}

class NeedForm(StyledModelForm):
    class Meta:
        model = UrgentNeed
        fields = ["title", "description", "resource_type", "quantity_needed", "status", "needed_by"]
        widgets = {"needed_by": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 3})}

class VolunteerProfileForm(StyledModelForm):
    class Meta:
        model = VolunteerProfile
        fields = ["phone", "skills", "availability_notes", "emergency_contact"]
        widgets = {"skills": forms.Textarea(attrs={"rows": 2}), "availability_notes": forms.Textarea(attrs={"rows": 2})}

class AssignTaskForm(forms.Form):
    membership = forms.ModelChoiceField(queryset=Membership.objects.none(), widget=forms.Select(attrs={"class": "form-control"}))
    def __init__(self, *args, **kwargs):
        organisation = kwargs.pop("organisation")
        super().__init__(*args, **kwargs)
        self.fields["membership"].queryset = Membership.objects.filter(organisation=organisation, is_active=True, role=Membership.Role.VOLUNTEER).select_related("user")
