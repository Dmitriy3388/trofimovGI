from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem
from mebel.models import Material

@receiver(post_save, sender=OrderItem)
def update_material_on_orderitem_save(sender, instance, created, **kwargs):
    """АКТУАЛИЗАЦИЯ: Обновляет резерв материала при сохранении OrderItem"""
    material = instance.material
    material.update_reserved_quantity()
    # Пересчитываем и сохраняем нехватку
    material.lack = max(0, material.reserved - material.balance)
    material.save(update_fields=['reserved', 'lack'])

@receiver(post_delete, sender=OrderItem)
def update_material_on_orderitem_delete(sender, instance, **kwargs):
    """АКТУАЛИЗАЦИЯ: Обновляет резерв материала при удалении OrderItem"""
    material = instance.material
    material.update_reserved_quantity()
    # Пересчитываем и сохраняем нехватку
    material.lack = max(0, material.reserved - material.balance)
    material.save(update_fields=['reserved', 'lack'])