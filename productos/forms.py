from django import forms
from django.core.exceptions import ValidationError

from .models import Categoria, ConsultaTienda, Producto, Resena, Tienda


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "imagen",
            "descripcion",
            "precio",
            "descuento",
            "envio_gratis",
            "stock",
            "tienda",
            "categoria",
            "activo",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "descuento": forms.NumberInput(attrs={"min": "0", "max": "100"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(activo=True)
        self.fields["tienda"].queryset = Tienda.objects.filter(activa=True)

        if user is not None and user.is_authenticated and not user.is_superuser:
            perfil = getattr(user, "perfil", None)
            if perfil and perfil.rol == "vendedor":
                self.fields["tienda"].queryset = Tienda.objects.filter(vendedor=user, activa=True)


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "activo"]


class TiendaForm(forms.ModelForm):
    class Meta:
        model = Tienda
        fields = [
            "nombre",
            "descripcion",
            "logo",
            "whatsapp",
            "activa",
        ]
        widgets = {
            "whatsapp": forms.TextInput(
                attrs={
                    "placeholder": "Ej: 5939XXXXXXXX",
                    "inputmode": "numeric",
                }
            ),
        }

    def clean_whatsapp(self):
        raw = self.cleaned_data.get("whatsapp", "")
        digits = "".join(ch for ch in str(raw) if ch.isdigit())

        # wa.me requiere formato internacional en solo dígitos.
        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                "Numero de WhatsApp invalido. Usa formato internacional (10 a 15 digitos), por ejemplo: 5939XXXXXXXX."
            )

        return digits


class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ["estrellas", "comentario"]
        widgets = {
            "comentario": forms.Textarea(attrs={"rows": 3, "placeholder": "Escribe tu comentario"}),
        }


class ConsultaTiendaForm(forms.ModelForm):
    class Meta:
        model = ConsultaTienda
        fields = ["mensaje"]
        widgets = {
            "mensaje": forms.Textarea(attrs={"rows": 3, "placeholder": "Escribe tu pregunta"}),
        }
