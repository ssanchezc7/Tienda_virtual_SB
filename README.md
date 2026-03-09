# Tienda Virtual con Pedido por WhatsApp (Python + Django)

Proyecto mobile-first para mostrar productos, agregar al carrito y enviar un pedido directo por WhatsApp.

## Requisitos

- Python 3.11+
- pip

## Instalación rápida

1. Crear entorno virtual:

   - Windows (PowerShell):
     - `python -m venv .venv`
     - `.\.venv\Scripts\Activate.ps1`

2. Instalar dependencias:

   - `pip install -r requirements.txt`

3. Ejecutar migraciones:

   - `python manage.py makemigrations`
   - `python manage.py migrate`

4. Crear usuario administrador:

   - `python manage.py createsuperuser`

5. Ejecutar servidor:

   - `python manage.py runserver`

## URLs

- Tienda: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/usuarios/login/
- Registro cliente: http://127.0.0.1:8000/usuarios/registro/
- Mis pedidos: http://127.0.0.1:8000/usuarios/mis-pedidos/

## Configuración clave

- Número de WhatsApp del vendedor:
  - Edita `whatsapp_numero` en la vista `lista_productos` dentro de [productos/views.py](productos/views.py).

## Funcionalidades incluidas

- Catálogo de productos
- Filtro por categoría y búsqueda
- Carrito con `localStorage`
- Cálculo automático de total
- Generación de mensaje para WhatsApp
- Enlace directo con `https://wa.me/`
- Roles de usuario: administrador, vendedor, cliente, invitado
- CRUD de vendedores (solo administrador)
- CRUD de productos (administrador y vendedor)
- Historial de pedidos para clientes registrados

## Sistema de usuarios y permisos

- `Administrador`:
   - Control total
   - Gestiona vendedores, productos, categorías y usuarios
   - Acceso a panel admin

- `Vendedor`:
   - Crea/edita/elimina sus propios productos
   - Gestiona stock, descuentos e imágenes
   - No puede gestionar usuarios ni vendedores

- `Cliente registrado`:
   - Se registra e inicia sesión
   - Compra productos
   - Guarda historial de pedidos

- `Invitado`:
   - Navega y agrega al carrito
   - Compra por WhatsApp sin cuenta
   - No guarda historial
