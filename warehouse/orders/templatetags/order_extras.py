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