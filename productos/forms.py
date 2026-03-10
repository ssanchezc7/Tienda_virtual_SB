from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Categoria, ConsultaTienda, Producto, Resena, Tienda

MAX_IMAGE_SIZE = 3 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_file(image):
    if not image:
        return image

    # En formularios de edicion, si no se sube una nueva imagen,
    # Django puede devolver un FieldFile/CloudinaryResource existente.
    # Solo validamos archivos realmente subidos en el request.
    if not isinstance(image, UploadedFile):
        return image

    content_type = getattr(image, "content_type", "")
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Formato de imagen no permitido. Usa JPG, PNG o WEBP.")

    try:
        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError("La imagen supera 3MB. Reduce su tamaño e intenta nuevamente.")
    except OSError:
        raise ValidationError("No se pudo leer el archivo de imagen. Intenta subirlo nuevamente.")

    return image


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "imagen",
            "imagen_secundaria",
            "imagen_detalle",
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
        self.fields["categoria"].queryset = Categoria.objects.filter(activo=True).select_related("parent").order_by("parent__nombre", "nombre")
        self.fields["tienda"].queryset = Tienda.objects.filter(activa=True)

        self.fields["categoria"].label_from_instance = (
            lambda categoria: f"- {categoria.nombre}" if categoria.parent else categoria.nombre
        )

        if user is not None and user.is_authenticated and not user.is_superuser:
           perfil = getattr(user, "perfil", None)

           if perfil and perfil.rol == "vendedor":
               qs = Tienda.objects.filter(vendedor=user, activa=True)

               if self.instance and self.instance.pk and self.instance.tienda:
                   qs = qs | Tienda.objects.filter(pk=self.instance.tienda.pk)

               self.fields["tienda"].queryset = qs.distinct()
        
            

    def clean_imagen(self):
        return validate_image_file(self.cleaned_data.get("imagen"))

    def clean_imagen_secundaria(self):
        return validate_image_file(self.cleaned_data.get("imagen_secundaria"))

    def clean_imagen_detalle(self):
        return validate_image_file(self.cleaned_data.get("imagen_detalle"))


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "parent", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].required = False
        self.fields["parent"].queryset = Categoria.objects.filter(activo=True, parent__isnull=True).order_by("nombre")


class TiendaForm(forms.ModelForm):
    class Meta:
        model = Tienda
        fields = [
            "nombre",
            "descripcion",
            "logo",
            "banner",
            "whatsapp",
            "ubicacion",
            "color_tema",
            "activa",
        ]
        widgets = {
            "whatsapp": forms.TextInput(
                attrs={
                    "placeholder": "Ej: 5939XXXXXXXX",
                    "inputmode": "numeric",
                }
            ),
            "ubicacion": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Guayaquil, Av. Principal y Calle 10",
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

    def clean_logo(self):
        return validate_image_file(self.cleaned_data.get("logo"))

    def clean_banner(self):
        return validate_image_file(self.cleaned_data.get("banner"))


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
