from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    crear_vendedor,
    eliminar_mi_cuenta,
    editar_mi_perfil_vendedor,
    editar_vendedor,
    eliminar_vendedor,
    lista_usuarios,
    login_view,
    mi_perfil,
    logout_view,
    mis_pedidos,
    registro_cliente,
)

app_name = "usuarios"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("mi-perfil/", mi_perfil, name="mi_perfil"),
    path("eliminar-cuenta/", eliminar_mi_cuenta, name="eliminar_mi_cuenta"),
    path("registro/", registro_cliente, name="registro"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/password_reset_form.html",
            email_template_name="usuarios/emails/password_reset_email.txt",
            subject_template_name="usuarios/emails/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("mis-pedidos/", mis_pedidos, name="mis_pedidos"),
    path("mi-perfil-vendedor/", editar_mi_perfil_vendedor, name="mi_perfil_vendedor"),
    path("admin/usuarios/", lista_usuarios, name="lista"),
    path("admin/usuarios/vendedores/nuevo/", crear_vendedor, name="crear_vendedor"),
    path("admin/usuarios/vendedores/<int:user_id>/editar/", editar_vendedor, name="editar_vendedor"),
    path("admin/usuarios/vendedores/<int:user_id>/eliminar/", eliminar_vendedor, name="eliminar_vendedor"),
]
