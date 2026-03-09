from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil


class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Sugerencia: usa un nombre corto, sin espacios y facil de recordar (ej: simon_store24)."
        self.fields["username"].widget.attrs.update({"placeholder": "Ejemplo: simon_store24"})

        self.fields["password1"].help_text = "Sugerencia: minimo 8 caracteres, combina mayusculas, minusculas, numeros y simbolos."
        self.fields["password1"].widget.attrs.update({"placeholder": "Crea una contrasena segura"})

        self.fields["password2"].help_text = "Sugerencia: repite exactamente la misma contrasena."
        self.fields["password2"].widget.attrs.update({"placeholder": "Repite tu contrasena"})


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario o correo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Usuario o correo"})
        self.fields["password"].widget.attrs.update({"placeholder": "Contrasena"})

    def clean(self):
        identificador = self.cleaned_data.get("username", "").strip()
        if identificador and "@" in identificador:
            user = User.objects.filter(email__iexact=identificador).first()
            if user:
                self.cleaned_data["username"] = user.username
        return super().clean()


class VendedorCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]


class VendedorUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active"]


class VendedorSelfUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class UsuarioCuentaForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class UsuarioPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["foto_perfil", "biografia"]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe algo sobre ti..."}),
        }


class PerfilVendedorForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["nombre_publico", "telefono", "foto_perfil", "foto_portada", "biografia"]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 3}),
        }


class PerfilRolForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["rol"]


class ConfirmarEliminacionCuentaForm(forms.Form):
    password = forms.CharField(
        label="Confirma tu contrasena",
        widget=forms.PasswordInput(attrs={"placeholder": "Ingresa tu contrasena actual"}),
    )
    confirmacion = forms.CharField(
        label="Escribe ELIMINAR para confirmar",
        help_text="Escribe exactamente: ELIMINAR",
        widget=forms.TextInput(attrs={"placeholder": "ELIMINAR"}),
    )

    def clean_confirmacion(self):
        valor = self.cleaned_data.get("confirmacion", "").strip()
        if valor != "ELIMINAR":
            raise forms.ValidationError("Debes escribir exactamente ELIMINAR para continuar.")
        return valor
