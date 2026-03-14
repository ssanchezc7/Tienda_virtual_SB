from django.urls import path

from .views import (
    actualizar_estado_pedido,
    crear_categoria,
    crear_consulta,
    crear_resena,
    crear_tienda,
    crear_producto,
    dashboard_vendedor,
    detalle_categoria,
    detalle_tienda,
    duplicar_producto,
    editar_categoria,
    editar_tienda,
    editar_producto,
    eliminar_categoria,
    eliminar_tienda,
    eliminar_producto,
    eliminar_resena,
    guardar_pedido,
    lista_categorias,
    lista_tiendas,
    lista_tiendas_gestion,
    lista_productos,
    toggle_favorito,
    toggle_activa_tienda,
    toggle_activo_producto,
)

app_name = "productos"

urlpatterns = [
    path("", lista_tiendas, name="home"),
    path("categoria/<slug:slug>/", detalle_categoria, name="detalle_categoria"),
    path("vendedor/dashboard/", dashboard_vendedor, name="dashboard_vendedor"),
    path("tienda/<int:pk>/", detalle_tienda, name="detalle_tienda"),
    path("tienda/<int:pk>/favorito/", toggle_favorito, name="toggle_favorito"),
    path("tienda/<int:pk>/resena/", crear_resena, name="crear_resena"),
    path("tienda/<int:pk>/consulta/", crear_consulta, name="crear_consulta"),

    path("productos/gestion/", lista_productos, name="lista"),
    path("productos/nuevo/", crear_producto, name="crear"),
    path("productos/<int:pk>/editar/", editar_producto, name="editar"),
    path("productos/<int:pk>/eliminar/", eliminar_producto, name="eliminar"),
    path("productos/<int:pk>/duplicar/", duplicar_producto, name="duplicar"),
    path("productos/<int:pk>/toggle-activo/", toggle_activo_producto, name="toggle_activo"),

    path("tiendas/gestion/", lista_tiendas_gestion, name="tiendas_gestion"),
    path("tiendas/nueva/", crear_tienda, name="crear_tienda"),
    path("tiendas/<int:pk>/editar/", editar_tienda, name="editar_tienda"),
    path("tiendas/<int:pk>/eliminar/", eliminar_tienda, name="eliminar_tienda"),
    path("tiendas/<int:pk>/toggle-activa/", toggle_activa_tienda, name="toggle_activa_tienda"),

    path("pedidos/guardar/", guardar_pedido, name="guardar_pedido"),
    path("pedidos/<int:pk>/estado/", actualizar_estado_pedido, name="actualizar_estado_pedido"),
    path("categorias/", lista_categorias, name="categorias"),
    path("categorias/nueva/", crear_categoria, name="crear_categoria"),
    path("categorias/<int:pk>/editar/", editar_categoria, name="editar_categoria"),
    path("categorias/<int:pk>/eliminar/", eliminar_categoria, name="eliminar_categoria"),
    path("resenas/<int:pk>/eliminar/", eliminar_resena, name="eliminar_resena"),
]
