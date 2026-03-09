from django.urls import path

from .views import (
    crear_vendedor,
    editar_mi_perfil_vendedor,
    editar_vendedor,
    eliminar_vendedor,
    lista_usuarios,
    login_view,
    logout_view,
    mis_pedidos,
    registro_cliente,
)

app_name = "usuarios"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("registro/", registro_cliente, name="registro"),
    path("mis-pedidos/", mis_pedidos, name="mis_pedidos"),
    path("mi-perfil-vendedor/", editar_mi_perfil_vendedor, name="mi_perfil_vendedor"),
    path("admin/usuarios/", lista_usuarios, name="lista"),
    path("admin/usuarios/vendedores/nuevo/", crear_vendedor, name="crear_vendedor"),
    path("admin/usuarios/vendedores/<int:user_id>/editar/", editar_vendedor, name="editar_vendedor"),
    path("admin/usuarios/vendedores/<int:user_id>/eliminar/", eliminar_vendedor, name="eliminar_vendedor"),
]
