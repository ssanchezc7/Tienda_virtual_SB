from django.contrib.auth.models import User
from django.db import models


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
    foto_perfil = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    foto_portada = models.ImageField(upload_to="portadas/", blank=True, null=True)
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
