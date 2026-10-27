from core.models import Membership

class MembershipContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.membership = None
        if request.user.is_authenticated:
            request.membership = Membership.objects.filter(user=request.user, is_active=True).select_related("organisation").first()
        return self.get_response(request)
