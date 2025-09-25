from django.db import models
from mebel.models import Material
from django.utils import timezone
from decimal import Decimal
from django.urls import reverse
from datetime import timedelta


class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        NOT_PAID = 'not_paid', 'Не оплачено'
        PARTIALLY_PAID = 'partially_paid', 'Оплачено частично'
        FULLY_PAID = 'fully_paid', 'Оплачено полностью'

    class InstallationStatus(models.TextChoices):
        NOT_INSTALLED = 'not_installed', 'Не установлено'
        INSTALLED = 'installed', 'Установлено'

    class CategoryChoices(models.TextChoices):
        KITCHEN = 'kitchen', 'Кухня'
        WARDROBE = 'wardrobe', 'Шкаф'
        TABLE = 'table', 'Стол'
        BED = 'bed', 'Кровать'
        OTHER = 'other', 'Другое'

    order_name = models.CharField(max_length=50, verbose_name='Название')
    customer_name = models.CharField(max_length=50, verbose_name='Имя заказчика')
    address = models.CharField(max_length=250)
    transferred_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                             verbose_name='Перечисленные средства')
    discount = models.PositiveIntegerField(default=0, verbose_name='Скидка (%)')
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        verbose_name='Категория'
    )
    deadline = models.DateField(
        default=timezone.now() + timedelta(days=1),  # Завтра по умолчанию
        verbose_name='Дата сдачи'
    )
    blueprint = models.ImageField(upload_to='blueprints/%Y/%m/%d/', blank=True, null=True, verbose_name='Чертеж')
    visualization = models.ImageField(upload_to='visualizations/%Y/%m/%d/', blank=True, null=True,
                                      verbose_name='Визуализация')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_PAID,
        verbose_name='Статус оплаты'
    )
    # Новые поля
    installation_status = models.CharField(
        max_length=20,
        choices=InstallationStatus.choices,
        default=InstallationStatus.NOT_INSTALLED,
        verbose_name='Установка'
    )
    installation_photo = models.ImageField(
        upload_to='installation_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Фото установки'
    )
    is_completed = models.BooleanField(default=False, verbose_name='Завершено')

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_write_off_url(self):
        return reverse('orders:order_write_off', args=[self.id])

    def get_total_cost(self):
        if not self.pk:
            return Decimal('0.00')
        materials_cost = sum(item.get_cost() for item in self.items.all())
        discount_decimal = Decimal(str(self.discount)) / Decimal('100')
        discount_multiplier = Decimal('1') - discount_decimal
        return materials_cost * Decimal('2') * discount_multiplier

    def get_deadline_status(self):
        """Возвращает статус сдачи заказа"""
        today = timezone.now().date()
        days_until_deadline = (self.deadline - today).days

        if days_until_deadline < 0:
            return {
                'status': 'просрочен',
                'class': 'danger',
                'icon': '❌'
            }
        elif days_until_deadline <= 14:  # Менее 2 недель
            return {
                'status': 'прогнозируется срыв',
                'class': 'warning',
                'icon': '⚠️'
            }
        else:
            return {
                'status': 'в работе',
                'class': 'success',
                'icon': '🛠️'
            }

    def update_payment_status(self):
        total_cost = self.get_total_cost()
        transferred = Decimal(str(self.transferred_amount))

        if transferred >= total_cost:
            self.paid = self.PaymentStatus.FULLY_PAID
        elif transferred > Decimal('0'):
            self.paid = self.PaymentStatus.PARTIALLY_PAID
        else:
            self.paid = self.PaymentStatus.NOT_PAID

    def update_completion_status(self):
        """Обновляет статус завершения заказа"""
        self.is_completed = (
            self.paid == self.PaymentStatus.FULLY_PAID and
            self.installation_status == self.InstallationStatus.INSTALLED
        )
    def save(self, *args, **kwargs):
        self.update_payment_status()
        self.update_completion_status()
        super().save(*args, **kwargs)



class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items',
                              on_delete=models.CASCADE)
    material = models.ForeignKey(Material,
                                related_name='order_items',
                                on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    written_off = models.PositiveIntegerField(default=0)
    operation_history = models.JSONField(default=list, blank=True)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

    from datetime import datetime

    def add_operation_to_history(self, operation_type, quantity, user, notes=None):
        """Добавляет операцию в историю"""
        operation = {
            'type': operation_type,
            'quantity': quantity,
            'user': user.username,
            'timestamp': timezone.now().isoformat(),  # Сохраняем как ISO строку
            'notes': notes
        }
        self.operation_history.append(operation)
        # Ограничиваем историю последними 10 операциями
        if len(self.operation_history) > 10:
            self.operation_history = self.operation_history[-10:]
        self.save(update_fields=['operation_history'])