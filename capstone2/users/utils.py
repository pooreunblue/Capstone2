from .models import User

def get_user_from_header(request):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    try:
        user_id = int(user_id)
        return User.objects.get(id=user_id)
    except (ValueError, User.DoesNotExist):
        return None