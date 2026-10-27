from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Membership, Organisation, VolunteerProfile

@receiver(post_save, sender=get_user_model())
def create_membership(sender, instance, created, **kwargs):
    if not created:
        return
    organisation = Organisation.objects.order_by("id").first()
    if organisation is None:
        organisation = Organisation.objects.create()
    role = Membership.Role.ADMIN if instance.is_superuser or instance.is_staff else Membership.Role.VOLUNTEER
    membership, membership_created = Membership.objects.get_or_create(organisation=organisation, user=instance, defaults={"role": role})
    if membership.role == Membership.Role.VOLUNTEER:
        VolunteerProfile.objects.get_or_create(membership=membership)
