from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Perfil


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil(sender, instance: User, created: bool, **kwargs) -> None:
    perfil, _ = Perfil.objects.get_or_create(user=instance)

    # Superusuario siempre se considera administrador.
    if instance.is_superuser and perfil.rol != Perfil.ROL_ADMIN:
        perfil.rol = Perfil.ROL_ADMIN
        perfil.save(update_fields=["rol"])
