from .models import OrderItem, Order
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum


# orders/signals.py - УНИФИЦИРОВАННАЯ ЛОГИКА
@receiver([post_save, post_delete], sender=OrderItem)
def update_material_reserve(sender, instance, **kwargs):
    material = instance.material
    total_reserved = OrderItem.objects.filter(
        material=material
    ).aggregate(total=Sum('quantity'))['total'] or 0

    if material.reserved != total_reserved:
        material.reserved = total_reserved
        material.lack = max(0, total_reserved - material.balance)
        material.save(update_fields=['reserved', 'lack'])

# Новый сигнал для обновления статуса завершения при изменении заказа
@receiver(post_save, sender=Order)
def update_order_completion_status(sender, instance, **kwargs):
    """Обновляет статус завершения при изменении заказа"""
    instance.update_completion_status()
    # Сохраняем только если статус изменился
    if instance.pk:
        Order.objects.filter(pk=instance.pk).update(is_completed=instance.is_completed)