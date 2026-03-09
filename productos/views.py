import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from usuarios.permissions import (
    admin_required,
    can_manage_products,
    is_seller,
    seller_or_admin_required,
    user_role,
)
from usuarios.models import Perfil

from .forms import CategoriaForm, ConsultaTiendaForm, ProductoForm, ResenaForm, TiendaForm
from .models import Categoria, ConsultaTienda, Favorito, Pedido, PedidoItem, Producto, Resena, Tienda


def lista_tiendas(request):
    tiendas = Tienda.objects.filter(activa=True).select_related("vendedor")
    populares = tiendas.order_by("-reputacion", "-calificacion")[:6]

    favoritas = Tienda.objects.none()
    if request.user.is_authenticated:
        favoritas = Tienda.objects.filter(favoritos__usuario=request.user, activa=True).distinct()

    context = {
        "populares": populares,
        "favoritas": favoritas,
        "tiendas": tiendas,
    }
    return render(request, "productos/lista_tiendas.html", context)


def detalle_tienda(request, pk):
    tienda = get_object_or_404(Tienda.objects.select_related("vendedor"), pk=pk, activa=True)

    categoria = request.GET.get("categoria", "")
    q = request.GET.get("q", "")
    productos = Producto.objects.filter(tienda=tienda, activo=True)

    if categoria:
        productos = productos.filter(categoria_id=categoria)

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

    favoritas = False
    if request.user.is_authenticated:
        favoritas = Favorito.objects.filter(usuario=request.user, tienda=tienda).exists()

    resenas = tienda.resenas.select_related("usuario")[:20]
    consultas = tienda.consultas.select_related("usuario")[:20]

    reseña_form = ResenaForm()
    consulta_form = ConsultaTiendaForm()

    context = {
        "tienda": tienda,
        "productos": productos,
        "categoria_actual": categoria,
        "q": q,
        "categorias": Categoria.objects.filter(activo=True),
        "is_favorita": favoritas,
        "resenas": resenas,
        "consultas": consultas,
        "resena_form": reseña_form,
        "consulta_form": consulta_form,
    }
    return render(request, "productos/detalle_tienda.html", context)


@login_required
@require_POST
def toggle_favorito(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk, activa=True)
    favorito = Favorito.objects.filter(usuario=request.user, tienda=tienda)
    if favorito.exists():
        favorito.delete()
        messages.info(request, "Tienda eliminada de favoritos.")
    else:
        Favorito.objects.create(usuario=request.user, tienda=tienda)
        messages.success(request, "Tienda agregada a favoritos.")
    return redirect("productos:detalle_tienda", pk=pk)


@login_required
@require_POST
def crear_resena(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk, activa=True)
    form = ResenaForm(request.POST)
    if form.is_valid():
        Resena.objects.update_or_create(
            usuario=request.user,
            tienda=tienda,
            defaults={
                "estrellas": form.cleaned_data["estrellas"],
                "comentario": form.cleaned_data["comentario"],
            },
        )
        tienda.actualizar_metricas()
        messages.success(request, "Resena guardada correctamente.")
    else:
        messages.error(request, "Datos invalidos para la resena.")
    return redirect("productos:detalle_tienda", pk=pk)


@login_required
@require_POST
def crear_consulta(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk, activa=True)
    form = ConsultaTiendaForm(request.POST)
    if form.is_valid():
        ConsultaTienda.objects.create(
            usuario=request.user,
            tienda=tienda,
            mensaje=form.cleaned_data["mensaje"],
        )
        messages.success(request, "Consulta enviada.")
    else:
        messages.error(request, "Escribe una consulta valida.")
    return redirect("productos:detalle_tienda", pk=pk)


@seller_or_admin_required
def lista_productos(request):
    estado = request.GET.get("estado", "todos")
    categoria = request.GET.get("categoria", "")
    q = request.GET.get("q", "")

    productos = Producto.objects.select_related("tienda", "categoria", "vendedor")
    if is_seller(request.user):
        productos = productos.filter(vendedor=request.user)

    if estado == "activos":
        productos = productos.filter(activo=True)
    elif estado == "inactivos":
        productos = productos.filter(activo=False)

    if categoria:
        productos = productos.filter(categoria_id=categoria)

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

    context = {
        "productos": productos,
        "categoria_actual": categoria,
        "estado_actual": estado,
        "q": q,
        "categorias": Categoria.objects.filter(activo=True),
    }
    return render(request, "productos/lista_productos.html", context)


@seller_or_admin_required
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            producto = form.save(commit=False)
            if is_seller(request.user):
                producto.vendedor = request.user
            producto.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("productos:lista")
        messages.error(request, "Revisa los campos del formulario.")
    else:
        form = ProductoForm(user=request.user)

    return render(request, "productos/crear_producto.html", {"form": form})


@seller_or_admin_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if is_seller(request.user) and producto.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes editar tus propios productos.")
        return redirect("productos:lista")

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("productos:lista")
        messages.error(request, "Revisa los campos del formulario.")
    else:
        form = ProductoForm(instance=producto, user=request.user)

    context = {"form": form, "producto": producto}
    return render(request, "productos/editar_producto.html", context)


@seller_or_admin_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if is_seller(request.user) and producto.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes eliminar tus propios productos.")
        return redirect("productos:lista")

    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto eliminado: {nombre}.")
        return redirect("productos:lista")

    return render(request, "productos/eliminar_producto.html", {"producto": producto})


@seller_or_admin_required
@require_POST
def toggle_activo_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if is_seller(request.user) and producto.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes gestionar tus propios productos.")
        return redirect("productos:lista")

    producto.activo = not producto.activo
    producto.save(update_fields=["activo"])

    estado = "activado" if producto.activo else "desactivado"
    messages.success(request, f"Producto {estado}: {producto.nombre}.")

    params = {}
    q = request.POST.get("q", "").strip()
    categoria = request.POST.get("categoria", "").strip()
    estado_filtro = request.POST.get("estado", "").strip()

    if q:
        params["q"] = q
    if categoria:
        params["categoria"] = categoria
    if estado_filtro and estado_filtro != "todos":
        params["estado"] = estado_filtro

    base_url = redirect("productos:lista").url
    if not params:
        return redirect(base_url)
    return redirect(f"{base_url}?{urlencode(params)}")


@login_required
@require_POST
def guardar_pedido(request):
    if user_role(request.user) != "cliente":
        return JsonResponse({"ok": False, "error": "Solo clientes registrados."}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Formato de pedido invalido."}, status=400)

    tienda_id = data.get("tienda_id")
    tienda = get_object_or_404(Tienda, pk=tienda_id, activa=True)

    items = data.get("items", [])
    total = Decimal(str(data.get("total", 0)))

    if not items:
        return JsonResponse({"ok": False, "error": "Carrito vacio."}, status=400)

    pedido = Pedido.objects.create(cliente=request.user, tienda=tienda, total=total)

    for item in items:
        producto_id = item.get("id")
        producto = get_object_or_404(Producto, pk=producto_id, tienda=tienda)
        cantidad = int(item.get("cantidad", 1))
        precio = Decimal(str(item.get("precio", 0)))
        subtotal = Decimal(str(item.get("subtotal", 0)))
        PedidoItem.objects.create(
            pedido=pedido,
            producto=producto,
            producto_nombre=producto.nombre,
            precio_unitario=precio,
            cantidad=max(1, cantidad),
            subtotal=subtotal,
        )

    tienda.total_ventas = tienda.total_ventas + 1
    tienda.actualizar_metricas()

    return JsonResponse({"ok": True, "pedido_id": pedido.id})


@admin_required
def lista_categorias(request):
    categorias = Categoria.objects.all().order_by("nombre")
    return render(request, "productos/lista_categorias.html", {"categorias": categorias})


@admin_required
def crear_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria creada correctamente.")
            return redirect("productos:categorias")
        messages.error(request, "Revisa los campos del formulario.")
    else:
        form = CategoriaForm()

    return render(request, "productos/form_categoria.html", {"form": form, "modo": "crear"})


@admin_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria actualizada correctamente.")
            return redirect("productos:categorias")
        messages.error(request, "Revisa los campos del formulario.")
    else:
        form = CategoriaForm(instance=categoria)

    return render(
        request,
        "productos/form_categoria.html",
        {"form": form, "modo": "editar", "categoria": categoria},
    )


@admin_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == "POST":
        productos_asociados = categoria.productos.count()
        if productos_asociados > 0:
            messages.error(
                request,
                f"No se puede eliminar la categoria '{categoria.nombre}' porque tiene {productos_asociados} producto(s) asociados.",
            )
            return redirect("productos:categorias")

        nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f"Categoria eliminada: {nombre}.")
        return redirect("productos:categorias")

    return render(request, "productos/eliminar_categoria.html", {"categoria": categoria})


@seller_or_admin_required
def lista_tiendas_gestion(request):
    tiendas = Tienda.objects.select_related("vendedor")
    if is_seller(request.user):
        tiendas = tiendas.filter(vendedor=request.user)
    return render(request, "productos/lista_tiendas_gestion.html", {"tiendas": tiendas})


@seller_or_admin_required
def crear_tienda(request):
    vendedores = User.objects.filter(perfil__rol=Perfil.ROL_VENDEDOR).order_by("username")

    if request.method == "POST":
        form = TiendaForm(request.POST, request.FILES)
        if form.is_valid():
            tienda = form.save(commit=False)
            if is_seller(request.user):
                tienda.vendedor = request.user
            else:
                vendedor_id = request.POST.get("vendedor_id")
                if vendedor_id:
                    tienda.vendedor_id = int(vendedor_id)
                else:
                    tienda.vendedor = request.user
            tienda.save()
            messages.success(request, "Tienda creada correctamente.")
            return redirect("productos:tiendas_gestion")
    else:
        form = TiendaForm()

    return render(
        request,
        "productos/form_tienda.html",
        {"form": form, "modo": "crear", "vendedores": vendedores},
    )


@seller_or_admin_required
def editar_tienda(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk)
    vendedores = User.objects.filter(perfil__rol=Perfil.ROL_VENDEDOR).order_by("username")
    if is_seller(request.user) and tienda.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes editar tus propias tiendas.")
        return redirect("productos:tiendas_gestion")

    if request.method == "POST":
        form = TiendaForm(request.POST, request.FILES, instance=tienda)
        if form.is_valid():
            if not is_seller(request.user):
                vendedor_id = request.POST.get("vendedor_id")
                if vendedor_id:
                    tienda.vendedor_id = int(vendedor_id)
            form.save()
            messages.success(request, "Tienda actualizada.")
            return redirect("productos:tiendas_gestion")
    else:
        form = TiendaForm(instance=tienda)

    return render(
        request,
        "productos/form_tienda.html",
        {"form": form, "modo": "editar", "tienda": tienda, "vendedores": vendedores},
    )


@seller_or_admin_required
def eliminar_tienda(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk)
    if is_seller(request.user) and tienda.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes eliminar tus propias tiendas.")
        return redirect("productos:tiendas_gestion")

    if request.method == "POST":
        productos_asociados = tienda.productos.count()
        if productos_asociados > 0:
            messages.error(
                request,
                f"No se puede eliminar la tienda '{tienda.nombre}' porque tiene {productos_asociados} producto(s). Desactiva la tienda o mueve sus productos.",
            )
            return redirect("productos:tiendas_gestion")

        nombre = tienda.nombre
        tienda.delete()
        messages.success(request, f"Tienda eliminada: {nombre}.")
        return redirect("productos:tiendas_gestion")

    return render(request, "productos/eliminar_tienda.html", {"tienda": tienda})


@seller_or_admin_required
@require_POST
def toggle_activa_tienda(request, pk):
    tienda = get_object_or_404(Tienda, pk=pk)
    if is_seller(request.user) and tienda.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes gestionar tus propias tiendas.")
        return redirect("productos:tiendas_gestion")

    tienda.activa = not tienda.activa
    tienda.save(update_fields=["activa"])

    estado = "activada" if tienda.activa else "desactivada"
    messages.success(request, f"Tienda {estado}: {tienda.nombre}.")
    return redirect("productos:tiendas_gestion")
