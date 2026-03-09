from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil


class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario")


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
        fields = ["username", "email", "first_name", "last_name"]


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
