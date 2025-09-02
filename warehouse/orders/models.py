from django.db import models
from mebel.models import Material


class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        NOT_PAID = 'not_paid', 'Не оплачено'
        PARTIALLY_PAID = 'partially_paid', 'Оплачено частично'
        FULLY_PAID = 'fully_paid', 'Оплачено полностью'

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_PAID,
        verbose_name='Статус оплаты'
    )

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())



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

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity