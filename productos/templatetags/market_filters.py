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
