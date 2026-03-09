from django import template

register = template.Library()


@register.filter
def stars(value):
    try:
        rating = float(value or 0)
    except (TypeError, ValueError):
        rating = 0

    rounded = int(round(rating))
    rounded = max(0, min(5, rounded))
    return ("★" * rounded) + ("☆" * (5 - rounded))


@register.filter
def category_icon(value):
    nombre = str(value or "").lower()

    if "tecnologia" in nombre or "computacion" in nombre:
        return "💻"
    if "celulares" in nombre:
        return "📱"
    if "electro" in nombre:
        return "🔌"
    if "ropa" in nombre or "moda" in nombre:
        return "👕"
    if "belleza" in nombre:
        return "💄"
    if "hogar" in nombre or "muebles" in nombre:
        return "🏠"
    if "deportes" in nombre or "fitness" in nombre:
        return "🏀"
    if "juguetes" in nombre:
        return "🧸"
    if "libros" in nombre:
        return "📚"
    if "vehiculos" in nombre:
        return "🚗"
    if "videojuegos" in nombre or "consolas" in nombre:
        return "🎮"
    return "🧩"
