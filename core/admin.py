from django.contrib import admin
from core.models import Donation, DonationReceipt, FundraisingCampaign, Membership, Organisation, Shift, ShiftBooking, Task, TaskAssignment, UrgentNeed, VolunteerProfile

admin.site.register(Organisation)
admin.site.register(Membership)
admin.site.register(VolunteerProfile)
admin.site.register(Donation)
admin.site.register(DonationReceipt)
admin.site.register(FundraisingCampaign)
admin.site.register(Shift)
admin.site.register(ShiftBooking)
admin.site.register(Task)
admin.site.register(TaskAssignment)
admin.site.register(UrgentNeed)
