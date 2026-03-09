from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategorias",
        blank=True,
        null=True,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["parent__nombre", "nombre"]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.nombre} > {self.nombre}"
        return self.nombre


class Tienda(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    logo = models.ImageField(upload_to="tiendas/", blank=True, null=True)
    banner = models.ImageField(upload_to="tiendas/banner/", blank=True, null=True)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tiendas")
    whatsapp = models.CharField(max_length=20)
    ubicacion = models.CharField(max_length=120, blank=True)
    color_tema = models.CharField(max_length=7, default="#0f766e")
    reputacion = models.FloatField(default=0)
    calificacion = models.FloatField(default=0)
    total_ventas = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["-reputacion", "-calificacion", "nombre"]

    def __str__(self) -> str:
        return self.nombre

    def actualizar_metricas(self) -> None:
        reviews = self.resenas.all()
        if not reviews.exists():
            self.calificacion = 0
            self.reputacion = 0
        else:
            promedio = sum(review.estrellas for review in reviews) / reviews.count()
            self.calificacion = round(promedio, 2)
            self.reputacion = round((self.calificacion * 0.7) + (min(self.total_ventas, 1000) / 1000 * 5 * 0.3), 2)
        self.save(update_fields=["calificacion", "reputacion"])


class Producto(models.Model):
    nombre = models.CharField(max_length=120)
    vendedor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="productos_publicados",
        blank=True,
        null=True,
    )
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.CASCADE,
        related_name="productos",
        blank=True,
        null=True,
    )
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    imagen_secundaria = models.ImageField(upload_to="productos/", blank=True, null=True)
    imagen_detalle = models.ImageField(upload_to="productos/", blank=True, null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.PositiveSmallIntegerField(default=0, help_text="Porcentaje 0-100")
    envio_gratis = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        blank=True,
        null=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def __str__(self) -> str:
        return self.nombre

    @property
    def precio_final(self) -> Decimal:
        if not self.descuento:
            return self.precio
        factor = Decimal(1) - (Decimal(self.descuento) / Decimal(100))
        return (self.precio * factor).quantize(Decimal("0.01"))


class Pedido(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_CONFIRMADO = "confirmado"
    ESTADO_VENDIDO = "vendido"
    ESTADO_ENTREGADO = "entregado"
    ESTADO_CANCELADO = "cancelado"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_CONFIRMADO, "Confirmado"),
        (ESTADO_VENDIDO, "Vendido"),
        (ESTADO_ENTREGADO, "Entregado"),
        (ESTADO_CANCELADO, "Cancelado"),
    ]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.SET_NULL,
        related_name="pedidos",
        blank=True,
        null=True,
    )
    codigo_vendedor = models.CharField(max_length=24, unique=True, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo_vendedor and self.pk:
            codigo = f"PED-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk, codigo_vendedor__isnull=True).update(codigo_vendedor=codigo)
            self.codigo_vendedor = codigo

    @property
    def referencia_vendedor(self) -> str:
        if self.codigo_vendedor:
            return self.codigo_vendedor
        if self.pk:
            return f"PED-{self.pk:06d}"
        return "PED-SIN-ID"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, blank=True, null=True)
    producto_nombre = models.CharField(max_length=120)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


class Resena(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resenas")
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="resenas")
    estrellas = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "tienda")
        ordering = ["-fecha_creacion"]


class Favorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tiendas_favoritas")
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="favoritos")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "tienda")


class ConsultaTienda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consultas_tienda")
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="consultas")
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]
