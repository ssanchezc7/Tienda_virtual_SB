import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Q, Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from urllib.parse import urlencode
from urllib.parse import quote_plus
from django.utils import timezone

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

MAX_TIENDAS_POR_VENDEDOR = 3


def lista_tiendas(request):
    busqueda_tienda = request.GET.get("tienda", "").strip()

    tiendas = Tienda.objects.filter(activa=True).select_related("vendedor")
    if busqueda_tienda:
        tiendas = tiendas.filter(Q(nombre__icontains=busqueda_tienda) | Q(descripcion__icontains=busqueda_tienda))

    populares = tiendas.order_by("-reputacion", "-calificacion")[:6]

    favoritas = Tienda.objects.none()
    if request.user.is_authenticated:
        favoritas = Tienda.objects.filter(favoritos__usuario=request.user, activa=True).distinct()

    categorias_base = Categoria.objects.filter(activo=True, parent__isnull=True).order_by("nombre")
    categorias_inicio = []
    categorias_destacadas = []

    for categoria in categorias_base:
        productos_categoria = Producto.objects.select_related("tienda", "categoria").filter(
            activo=True,
            tienda__activa=True,
        ).filter(Q(categoria=categoria) | Q(categoria__parent=categoria))

        total = productos_categoria.count()
        if total == 0:
            continue

        categorias_inicio.append(
            {
                "categoria": categoria,
                "total": total,
                "slug": slugify(categoria.nombre),
            }
        )

        if len(categorias_destacadas) < 4:
            categorias_destacadas.append(
                {
                    "categoria": categoria,
                    "slug": slugify(categoria.nombre),
                    "productos": productos_categoria.order_by("-fecha_creacion")[:3],
                }
            )

    context = {
        "populares": populares,
        "favoritas": favoritas,
        "tiendas": tiendas,
        "busqueda_tienda": busqueda_tienda,
        "categorias_inicio": categorias_inicio,
        "categorias_destacadas": categorias_destacadas,
    }
    return render(request, "productos/lista_tiendas.html", context)


def detalle_categoria(request, slug):
    categorias_base = Categoria.objects.filter(activo=True, parent__isnull=True)
    categoria = None
    for item in categorias_base:
        if slugify(item.nombre) == slug:
            categoria = item
            break

    if not categoria:
        categoria = get_object_or_404(Categoria, activo=True)

    ordenar = request.GET.get("orden", "recientes")
    subcategoria_id = request.GET.get("subcategoria", "").strip()
    order_map = {
        "recientes": "-fecha_creacion",
        "baratos": "precio",
        "caros": "-precio",
        "calificados": "-tienda__calificacion",
    }
    order_by = order_map.get(ordenar, "-fecha_creacion")

    productos = Producto.objects.select_related("tienda", "categoria").filter(
        activo=True,
        tienda__activa=True,
    )

    subcategorias = Categoria.objects.filter(parent=categoria, activo=True).order_by("nombre")
    subcategoria_actual = None

    if subcategoria_id:
        subcategoria_actual = subcategorias.filter(id=subcategoria_id).first()
        if subcategoria_actual:
            productos = productos.filter(categoria=subcategoria_actual)
        else:
            productos = productos.filter(Q(categoria=categoria) | Q(categoria__parent=categoria))
            subcategoria_id = ""
    else:
        productos = productos.filter(Q(categoria=categoria) | Q(categoria__parent=categoria))

    productos = productos.order_by(order_by, "-fecha_creacion")

    context = {
        "categoria": categoria,
        "subcategorias": subcategorias,
        "productos": productos,
        "orden_actual": ordenar,
        "subcategoria_actual": subcategoria_id,
        "subcategoria_obj": subcategoria_actual,
        "total_productos": productos.count(),
    }
    return render(request, "productos/detalle_categoria.html", context)


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
    can_edit_tienda = False
    if request.user.is_authenticated:
        favoritas = Favorito.objects.filter(usuario=request.user, tienda=tienda).exists()
        rol = user_role(request.user)
        can_edit_tienda = rol == "administrador" or (rol == "vendedor" and tienda.vendedor_id == request.user.id)

    resenas = tienda.resenas.select_related("usuario", "usuario__perfil")[:20]
    consultas = tienda.consultas.select_related("usuario", "usuario__perfil")[:20]

    reseña_form = ResenaForm()
    consulta_form = ConsultaTiendaForm()

    context = {
        "tienda": tienda,
        "productos": productos,
        "total_favoritos": tienda.favoritos.count(),
        "categoria_actual": categoria,
        "q": q,
        "categorias": Categoria.objects.filter(activo=True),
        "is_favorita": favoritas,
        "can_edit_tienda": can_edit_tienda,
        "resenas": resenas,
        "consultas": consultas,
        "resena_form": reseña_form,
        "consulta_form": consulta_form,
        "ubicacion_maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(tienda.ubicacion)}" if tienda.ubicacion else "",
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
def dashboard_vendedor(request):
    # Para admin se muestra un consolidado global; para vendedor sus propios datos.
    tiendas_qs = Tienda.objects.all()
    productos_qs = Producto.objects.select_related("tienda")
    pedidos_qs = Pedido.objects.select_related("tienda")
    resenas_qs = Resena.objects.select_related("usuario", "usuario__perfil", "tienda")
    consultas_qs = ConsultaTienda.objects.select_related("usuario", "usuario__perfil", "tienda")
    pedido_items_qs = PedidoItem.objects.select_related("pedido")

    if is_seller(request.user):
        tiendas_qs = tiendas_qs.filter(vendedor=request.user)
        productos_qs = productos_qs.filter(vendedor=request.user)
        pedidos_qs = pedidos_qs.filter(tienda__vendedor=request.user)
        resenas_qs = resenas_qs.filter(tienda__vendedor=request.user)
        consultas_qs = consultas_qs.filter(tienda__vendedor=request.user)
        pedido_items_qs = pedido_items_qs.filter(pedido__tienda__vendedor=request.user)

    tienda_filtro = request.GET.get("tienda", "").strip()
    pedido_query = request.GET.get("pedido", "").strip()
    estado_filtro = request.GET.get("estado_pedido", "todos").strip() or "todos"
    if tienda_filtro:
        tiendas_qs = tiendas_qs.filter(id=tienda_filtro)
        productos_qs = productos_qs.filter(tienda_id=tienda_filtro)
        pedidos_qs = pedidos_qs.filter(tienda_id=tienda_filtro)
        resenas_qs = resenas_qs.filter(tienda_id=tienda_filtro)
        consultas_qs = consultas_qs.filter(tienda_id=tienda_filtro)
        pedido_items_qs = pedido_items_qs.filter(pedido__tienda_id=tienda_filtro)

    if pedido_query:
        if pedido_query.isdigit():
            pedidos_qs = pedidos_qs.filter(Q(id=int(pedido_query)) | Q(codigo_vendedor__icontains=pedido_query))
        else:
            pedidos_qs = pedidos_qs.filter(codigo_vendedor__icontains=pedido_query)

    if estado_filtro != "todos":
        pedidos_qs = pedidos_qs.filter(estado=estado_filtro)

    total_productos = productos_qs.count()
    productos_activos = productos_qs.filter(activo=True).count()
    pedidos_recibidos = pedidos_qs.count()
    pedidos_pendientes = pedidos_qs.filter(estado=Pedido.ESTADO_PENDIENTE).count()
    pedidos_confirmados = pedidos_qs.filter(estado=Pedido.ESTADO_CONFIRMADO).count()
    pedidos_vendidos = pedidos_qs.filter(estado=Pedido.ESTADO_VENDIDO).count()
    pedidos_entregados = pedidos_qs.filter(estado=Pedido.ESTADO_ENTREGADO).count()
    pedidos_cancelados = pedidos_qs.filter(estado=Pedido.ESTADO_CANCELADO).count()
    total_comentarios = consultas_qs.count()
    total_resenas = resenas_qs.count()
    rating_promedio = resenas_qs.aggregate(avg=Avg("estrellas")).get("avg") or 0

    hoy = timezone.now()
    pedidos_mes = pedidos_qs.filter(fecha_creacion__year=hoy.year, fecha_creacion__month=hoy.month).count()

    top_productos = (
        pedido_items_qs.values("producto_nombre")
        .annotate(total_vendidos=Sum("cantidad"))
        .order_by("-total_vendidos")[:5]
    )
    top_productos = list(top_productos)
    max_top_vendidos = top_productos[0]["total_vendidos"] if top_productos else 1

    latest_resenas = resenas_qs.order_by("-fecha_creacion")[:5]
    latest_consultas = consultas_qs.order_by("-fecha_creacion")[:5]
    pedidos_ordenados = pedidos_qs.select_related("cliente", "tienda").order_by("-fecha_creacion")
    latest_pedidos = pedidos_ordenados[:8]

    paginator = Paginator(pedidos_ordenados, 10)
    page_number = request.GET.get("page")
    pedidos_page = paginator.get_page(page_number)

    context = {
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "pedidos_recibidos": pedidos_recibidos,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_confirmados": pedidos_confirmados,
        "pedidos_vendidos": pedidos_vendidos,
        "pedidos_entregados": pedidos_entregados,
        "pedidos_cancelados": pedidos_cancelados,
        "total_comentarios": total_comentarios,
        "total_resenas": total_resenas,
        "rating_promedio": round(float(rating_promedio), 2),
        "pedidos_mes": pedidos_mes,
        "top_productos": top_productos,
        "max_top_vendidos": max_top_vendidos,
        "latest_resenas": latest_resenas,
        "latest_consultas": latest_consultas,
        "latest_pedidos": latest_pedidos,
        "pedidos_page": pedidos_page,
        "estados_pedido": Pedido.ESTADOS,
        "tiendas": tiendas_qs.order_by("-fecha_creacion")[:6],
        "tiendas_filtro": Tienda.objects.filter(vendedor=request.user).order_by("nombre") if is_seller(request.user) else Tienda.objects.order_by("nombre"),
        "tienda_filtro": tienda_filtro,
        "pedido_query": pedido_query,
        "estado_filtro": estado_filtro,
    }
    return render(request, "productos/dashboard_vendedor.html", context)


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


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    # Verificar que el usuario pueda editar el producto.
    if not request.user.is_superuser:
        vendedor_producto = producto.tienda.vendedor if producto.tienda else producto.vendedor
        if vendedor_producto != request.user:
            messages.error(request, "No tienes permiso para editar este producto.")
            return redirect("productos:lista")

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("productos:lista")
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
def duplicar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if is_seller(request.user) and producto.vendedor_id != request.user.id:
        messages.error(request, "Solo puedes duplicar tus propios productos.")
        return redirect("productos:lista")

    copia = Producto.objects.create(
        nombre=f"{producto.nombre} (Copia)",
        vendedor=producto.vendedor,
        tienda=producto.tienda,
        imagen=producto.imagen,
        imagen_secundaria=producto.imagen_secundaria,
        imagen_detalle=producto.imagen_detalle,
        descripcion=producto.descripcion,
        precio=producto.precio,
        descuento=producto.descuento,
        envio_gratis=producto.envio_gratis,
        stock=producto.stock,
        categoria=producto.categoria,
        activo=False,
    )
    messages.success(request, f"Producto duplicado: {copia.nombre}.")
    return redirect("productos:editar", pk=copia.pk)


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

    if not items:
        return JsonResponse({"ok": False, "error": "Carrito vacio."}, status=400)

    try:
        items_normalizados = []
        for item in items:
            producto_id = int(item.get("id"))
            cantidad = int(item.get("cantidad", 1))
            if cantidad <= 0:
                return JsonResponse({"ok": False, "error": "Cantidad invalida en carrito."}, status=400)
            items_normalizados.append({"id": producto_id, "cantidad": cantidad})
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Datos de carrito invalidos."}, status=400)

    with transaction.atomic():
        ids = [item["id"] for item in items_normalizados]
        productos = (
            Producto.objects.select_for_update()
            .filter(pk__in=ids, tienda=tienda, activo=True)
        )
        productos_map = {producto.id: producto for producto in productos}

        faltantes = [item for item in items_normalizados if item["id"] not in productos_map]
        if faltantes:
            return JsonResponse(
                {"ok": False, "error": "Hay productos no disponibles en este momento."},
                status=400,
            )

        sin_stock = []
        lineas_pedido = []
        total_real = Decimal("0.00")

        for item in items_normalizados:
            producto = productos_map[item["id"]]
            cantidad = item["cantidad"]

            if producto.stock is not None and cantidad > producto.stock:
                sin_stock.append({"producto": producto.nombre, "stock": producto.stock})
                continue

            precio_unitario = producto.precio_final
            subtotal = (precio_unitario * Decimal(cantidad)).quantize(Decimal("0.01"))
            total_real += subtotal

            lineas_pedido.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal,
                }
            )

        if sin_stock:
            nombre = sin_stock[0]["producto"]
            return JsonResponse(
                {
                    "ok": False,
                    "error": f"Stock insuficiente para {nombre}. Actualiza tu carrito.",
                    "detalle": sin_stock,
                },
                status=400,
            )

        pedido = Pedido.objects.create(cliente=request.user, tienda=tienda, total=total_real)

        for linea in lineas_pedido:
            producto = linea["producto"]
            cantidad = linea["cantidad"]

            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                producto_nombre=producto.nombre,
                precio_unitario=linea["precio_unitario"],
                cantidad=cantidad,
                subtotal=linea["subtotal"],
            )

            if producto.stock is not None:
                producto.stock = max(0, producto.stock - cantidad)
                if producto.stock == 0:
                    producto.activo = False
                producto.save(update_fields=["stock", "activo"])

        tienda.total_ventas = tienda.total_ventas + 1
        tienda.save(update_fields=["total_ventas"])
        tienda.actualizar_metricas()

    return JsonResponse({"ok": True, "pedido_id": pedido.id, "pedido_codigo": pedido.referencia_vendedor})


@seller_or_admin_required
@require_POST
def actualizar_estado_pedido(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("tienda"), pk=pk)

    if is_seller(request.user):
        if not pedido.tienda or pedido.tienda.vendedor_id != request.user.id:
            messages.error(request, "No puedes cambiar pedidos de otras tiendas.")
            return redirect("productos:dashboard_vendedor")

    estado = request.POST.get("estado", "").strip()
    estados_validos = {valor for valor, _ in Pedido.ESTADOS}
    if estado not in estados_validos:
        messages.error(request, "Estado de pedido invalido.")
        return redirect("productos:dashboard_vendedor")

    pedido.estado = estado
    pedido.save(update_fields=["estado"])
    messages.success(request, f"Pedido #{pedido.id} actualizado a {pedido.get_estado_display()}.")

    tienda_filtro = request.POST.get("tienda", "").strip()
    pedido_query = request.POST.get("pedido", "").strip()
    estado_filtro = request.POST.get("estado_pedido", "").strip()
    params = {}
    if tienda_filtro:
        params["tienda"] = tienda_filtro
    if pedido_query:
        params["pedido"] = pedido_query
    if estado_filtro:
        params["estado_pedido"] = estado_filtro

    base_url = redirect("productos:dashboard_vendedor").url
    if params:
        return redirect(f"{base_url}?{urlencode(params)}")
    return redirect("productos:dashboard_vendedor")


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
    cantidad_tiendas_vendedor = 0
    limite_tiendas_alcanzado = False

    if is_seller(request.user):
        tiendas = tiendas.filter(vendedor=request.user)
        cantidad_tiendas_vendedor = tiendas.count()
        limite_tiendas_alcanzado = cantidad_tiendas_vendedor >= MAX_TIENDAS_POR_VENDEDOR

    context = {
        "tiendas": tiendas,
        "cantidad_tiendas_vendedor": cantidad_tiendas_vendedor,
        "max_tiendas_vendedor": MAX_TIENDAS_POR_VENDEDOR,
        "limite_tiendas_alcanzado": limite_tiendas_alcanzado,
    }
    return render(request, "productos/lista_tiendas_gestion.html", context)


@seller_or_admin_required
def crear_tienda(request):
    vendedores = User.objects.filter(perfil__rol=Perfil.ROL_VENDEDOR).order_by("username")

    if is_seller(request.user):
        cantidad_actual = Tienda.objects.filter(vendedor=request.user).count()
        if cantidad_actual >= MAX_TIENDAS_POR_VENDEDOR:
            messages.error(
                request,
                f"Has alcanzado el limite de {MAX_TIENDAS_POR_VENDEDOR} tiendas. No puedes crear mas.",
            )
            return redirect("productos:tiendas_gestion")

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


@seller_or_admin_required
@require_POST
def eliminar_resena(request, pk):
    resena = get_object_or_404(Resena, pk=pk)
    # Solo admin o vendedor de la tienda pueden eliminar
    es_admin = request.user.is_superuser or user_role(request.user) == "administrador"
    es_vendedor = user_role(request.user) == "vendedor" and resena.tienda.vendedor_id == request.user.id
    if not (es_admin or es_vendedor):
        messages.error(request, "No tienes permiso para eliminar esta reseña.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    resena.delete()
    messages.success(request, "Reseña eliminada correctamente.")
    return redirect(request.META.get("HTTP_REFERER", "/"))
