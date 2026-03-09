from django.db import migrations, models


def seed_categories(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")

    top_level = [
        "Tecnologia",
        "Celulares y accesorios",
        "Computacion",
        "Electrodomesticos",
        "Ropa y moda",
        "Belleza y cuidado personal",
        "Hogar y muebles",
        "Deportes y fitness",
        "Juguetes",
        "Libros",
        "Vehiculos y accesorios",
        "Otros",
    ]

    for nombre in top_level:
        Categoria.objects.get_or_create(nombre=nombre, defaults={"activo": True})

    subcategorias = {
        "Tecnologia": ["Audifonos", "Mouse", "Teclados", "Camaras", "Consolas"],
        "Ropa y moda": ["Camisetas", "Pantalones", "Zapatos", "Accesorios"],
        "Hogar y muebles": ["Cocina", "Decoracion", "Muebles", "Iluminacion"],
    }

    for parent_name, children in subcategorias.items():
        parent = Categoria.objects.filter(nombre=parent_name).first()
        if not parent:
            continue
        for child_name in children:
            Categoria.objects.get_or_create(
                nombre=child_name,
                defaults={"parent": parent, "activo": True},
            )


def noop_reverse(apps, schema_editor):
    # No elimina datos para evitar borrar categorias creadas por usuarios.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0005_pedido_codigo_vendedor_alter_pedido_estado"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="subcategorias",
                to="productos.categoria",
            ),
        ),
        migrations.RunPython(seed_categories, noop_reverse),
    ]
