from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from productos.models import Pedido

from .forms import (
    LoginForm,
    PerfilVendedorForm,
    RegistroClienteForm,
    VendedorCreateForm,
    VendedorSelfUpdateForm,
    VendedorUpdateForm,
)
from .models import Perfil
from .permissions import admin_required, is_seller


def registro_cliente(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("productos:home")

    if request.method == "POST":
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            perfil, _ = Perfil.objects.get_or_create(user=user)
            perfil.rol = Perfil.ROL_CLIENTE
            perfil.save(update_fields=["rol"])
            login(request, user)
            messages.success(request, "Cuenta creada correctamente.")
            return redirect("productos:home")
    else:
        form = RegistroClienteForm()

    return render(request, "usuarios/registro.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("productos:home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Sesion iniciada.")
            return redirect("productos:home")
    else:
        form = LoginForm(request)

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "Sesion cerrada.")
    return redirect("productos:home")


@admin_required
def lista_usuarios(request: HttpRequest) -> HttpResponse:
    perfiles = Perfil.objects.select_related("user").order_by("user__username")
    vendedores = [p for p in perfiles if p.rol == Perfil.ROL_VENDEDOR]
    clientes = [p for p in perfiles if p.rol == Perfil.ROL_CLIENTE]
    return render(
        request,
        "usuarios/lista_usuarios.html",
        {"vendedores": vendedores, "clientes": clientes},
    )


@admin_required
def crear_vendedor(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = VendedorCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.is_staff = False
            user.save()
            perfil, _ = Perfil.objects.get_or_create(user=user)
            perfil.rol = Perfil.ROL_VENDEDOR
            perfil.save(update_fields=["rol"])
            messages.success(request, "Vendedor creado correctamente.")
            return redirect("usuarios:lista")
    else:
        form = VendedorCreateForm()

    return render(request, "usuarios/form_vendedor.html", {"form": form, "modo": "crear"})


@admin_required
def editar_vendedor(request: HttpRequest, user_id: int) -> HttpResponse:
    user = get_object_or_404(User, pk=user_id)
    perfil, _ = Perfil.objects.get_or_create(user=user)
    if perfil.rol != Perfil.ROL_VENDEDOR:
        messages.error(request, "El usuario seleccionado no es vendedor.")
        return redirect("usuarios:lista")

    if request.method == "POST":
        user_form = VendedorUpdateForm(request.POST, instance=user)
        perfil_form = PerfilVendedorForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Vendedor actualizado.")
            return redirect("usuarios:lista")
    else:
        user_form = VendedorUpdateForm(instance=user)
        perfil_form = PerfilVendedorForm(instance=perfil)

    return render(
        request,
        "usuarios/form_vendedor.html",
        {"user_form": user_form, "perfil_form": perfil_form, "modo": "editar", "vendedor": user},
    )


@login_required
def editar_mi_perfil_vendedor(request: HttpRequest) -> HttpResponse:
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    if not is_seller(request.user):
        messages.error(request, "Esta seccion es solo para vendedores.")
        return redirect("productos:home")

    if request.method == "POST":
        user_form = VendedorSelfUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilVendedorForm(request.POST, request.FILES, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("usuarios:mi_perfil_vendedor")
    else:
        user_form = VendedorSelfUpdateForm(instance=request.user)
        perfil_form = PerfilVendedorForm(instance=perfil)

    return render(
        request,
        "usuarios/perfil_vendedor.html",
        {"user_form": user_form, "perfil_form": perfil_form},
    )


@admin_required
def eliminar_vendedor(request: HttpRequest, user_id: int) -> HttpResponse:
    user = get_object_or_404(User, pk=user_id)
    perfil, _ = Perfil.objects.get_or_create(user=user)
    if perfil.rol != Perfil.ROL_VENDEDOR:
        messages.error(request, "El usuario seleccionado no es vendedor.")
        return redirect("usuarios:lista")

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"Vendedor eliminado: {username}.")
        return redirect("usuarios:lista")

    return render(request, "usuarios/eliminar_vendedor.html", {"vendedor": user})


def mis_pedidos(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesion para ver tu historial.")
        return redirect("usuarios:login")

    pedidos = Pedido.objects.filter(cliente=request.user).prefetch_related("items").order_by("-fecha_creacion")
    return render(request, "usuarios/mis_pedidos.html", {"pedidos": pedidos})
