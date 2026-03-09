from django.contrib.auth.models import User
from django.db import models
from cloudinary.models import CloudinaryField

class Perfil(models.Model):
    ROL_ADMIN = "administrador"
    ROL_VENDEDOR = "vendedor"
    ROL_CLIENTE = "cliente"

    ROLES = [
        (ROL_ADMIN, "Administrador"),
        (ROL_VENDEDOR, "Vendedor"),
        (ROL_CLIENTE, "Cliente registrado"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_CLIENTE)
    nombre_publico = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    foto_perfil = CloudinaryField("foto_perfil", blank=True, null=True)
    foto_portada = CloudinaryField("foto_portada", blank=True, null=True)
    biografia = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_rol_display()})"

    @property
    def es_admin(self) -> bool:
        return self.rol == self.ROL_ADMIN

    @property
    def es_vendedor(self) -> bool:
        return self.rol == self.ROL_VENDEDOR

    @property
    def es_cliente(self) -> bool:
        return self.rol == self.ROL_CLIENTE
