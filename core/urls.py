from django.urls import path
from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("donations/", views.donations, name="donations"),
    path("donations/<int:donation_id>/receipt/", views.receipt_pdf, name="receipt_pdf"),
    path("campaigns/", views.campaigns, name="campaigns"),
    path("campaigns/<int:campaign_id>/status/",views.update_campaign_status,name="update_campaign_status",
),

    path("shifts/", views.shifts, name="shifts"),
    path("shifts/<int:shift_id>/book/", views.book_shift, name="book_shift"),
    path("bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("tasks/", views.tasks, name="tasks"),
    path("tasks/<int:task_id>/assign/", views.assign_task, name="assign_task"),
    path("tasks/<int:task_id>/status/", views.update_task_status, name="update_task_status"),
    path("needs/", views.needs, name="needs"),
    path("reports/", views.reports, name="reports"),
    path("members/", views.members, name="members"),
    path("members/<int:membership_id>/role/", views.change_member_role, name="change_member_role"),
]
