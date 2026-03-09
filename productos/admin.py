from django.contrib import admin

from .models import (
    Categoria,
    ConsultaTienda,
    Favorito,
    Pedido,
    PedidoItem,
    Producto,
    Resena,
    Tienda,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "vendedor",
        "tienda",
        "categoria",
        "precio",
        "descuento",
        "envio_gratis",
        "stock",
        "activo",
    )
    list_filter = ("categoria", "envio_gratis", "activo")
    search_fields = ("nombre", "descripcion")
    list_editable = ("precio", "descuento", "stock", "activo")


class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "tienda", "total", "fecha_creacion")
    list_filter = ("fecha_creacion",)
    search_fields = ("cliente__username",)
    inlines = [PedidoItemInline]


@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "vendedor", "whatsapp", "calificacion", "reputacion", "total_ventas", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "vendedor__username", "whatsapp")


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("tienda", "usuario", "estrellas", "fecha_creacion")
    list_filter = ("estrellas",)
    search_fields = ("tienda__nombre", "usuario__username")


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tienda", "fecha_creacion")


@admin.register(ConsultaTienda)
class ConsultaTiendaAdmin(admin.ModelAdmin):
    list_display = ("tienda", "usuario", "fecha_creacion")
    search_fields = ("tienda__nombre", "usuario__username", "mensaje")
