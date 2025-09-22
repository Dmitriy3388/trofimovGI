from django import template
from mebel.models import Material

register = template.Library()

@register.filter
def get_material_price(material_id):
    """Возвращает цену материала по его ID"""
    try:
        material = Material.objects.get(id=material_id)
        return material.price
    except Material.DoesNotExist:
        return 0

@register.filter
def subtract(value, arg):
    """Вычитает arg из value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value