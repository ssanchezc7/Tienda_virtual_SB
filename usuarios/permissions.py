from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Perfil


def user_role(user) -> str:
    if not user.is_authenticated:
        return "invitado"

    if user.is_superuser:
        perfil, _ = Perfil.objects.get_or_create(user=user)
        if perfil.rol != Perfil.ROL_ADMIN:
            perfil.rol = Perfil.ROL_ADMIN
            perfil.save(update_fields=["rol"])
        return Perfil.ROL_ADMIN

    perfil, _ = Perfil.objects.get_or_create(user=user)
    return perfil.rol


def is_admin(user) -> bool:
    return user.is_authenticated and user_role(user) == Perfil.ROL_ADMIN


def is_seller(user) -> bool:
    return user.is_authenticated and user_role(user) == Perfil.ROL_VENDEDOR


def can_manage_products(user) -> bool:
    return is_admin(user) or is_seller(user)


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Acceso solo para administradores.")
            return redirect("productos:home")
        return view_func(request, *args, **kwargs)

    return _wrapped


def seller_or_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not can_manage_products(request.user):
            messages.error(request, "Acceso solo para vendedores o administradores.")
            return redirect("productos:home")
        return view_func(request, *args, **kwargs)

    return _wrapped
