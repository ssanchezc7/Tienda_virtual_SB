from django.db.models import Q
from django.utils.text import slugify

from .models import Categoria, Producto


def categories_menu(request):
    categorias = Categoria.objects.filter(activo=True, parent__isnull=True).order_by("nombre")[:10]

    menu = []
    for categoria in categorias:
        total = Producto.objects.filter(
            activo=True,
            tienda__activa=True,
        ).filter(Q(categoria=categoria) | Q(categoria__parent=categoria)).count()

        menu.append(
            {
                "id": categoria.id,
                "nombre": categoria.nombre,
                "slug": slugify(categoria.nombre),
                "total": total,
            }
        )

    return {"menu_categorias": menu}
