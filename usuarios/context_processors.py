from .permissions import can_manage_products, is_admin, user_role


def role_context(request):
    role = user_role(request.user)
    return {
        "role_name": role,
        "is_admin_role": is_admin(request.user),
        "can_manage_products": can_manage_products(request.user),
    }
