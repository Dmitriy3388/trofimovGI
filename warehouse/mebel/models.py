from django.db import models
from django.urls import reverse
from django.db.models import Sum
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from transliterate import slugify as transliterate_slugify
from django.db.models.functions import Lower, Replace
from django.db.models import Value
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название поставщика")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Контактное лицо")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Адрес")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mebel:supplier_detail', args=[self.id])

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200,
                            unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower(Replace('name', Value(' '), Value(''))),
                name='unique_normalized_name'
            )
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mebel:material_list_by_category',
                       args=[self.slug])


class Material(models.Model):
    category = models.ForeignKey(Category,
                                 related_name='materials',
                                 on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    image = models.ImageField(upload_to='materials/%Y/%m/%d',
                              blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
    supplier = models.ForeignKey(Supplier,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                verbose_name="Поставщик",
                                related_name='materials')
    balance = models.PositiveIntegerField(default=0, verbose_name="Текущий остаток")
    reserved = models.PositiveIntegerField(default=0, verbose_name="Зарезервировано")
    lack = models.PositiveIntegerField(default=0, verbose_name="Нехватка")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['lack']),
        ]

    def get_write_off_url(self):
        return reverse('mebel:material_write_off', args=[self.id])

    def get_receipt_url(self):
        return reverse('mebel:material_receipt', args=[self.id])

    @classmethod
    def recalculate_balance(cls, material_id):
        from django.db.models import Sum

        material = cls.objects.get(id=material_id)
        total_receipt = MaterialOperation.objects.filter(
            material=material,
            operation_type='receipt'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        total_write_off = MaterialOperation.objects.filter(
            material=material,
            operation_type='write_off'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        new_balance = total_receipt - total_write_off
        if material.balance != new_balance:
            material.balance = new_balance
            material.save(update_fields=['balance'])

        return new_balance

    @classmethod
    def recalculate_all_balances(cls):
        """Пересчитывает балансы для всех материалов"""
        for material in cls.objects.all():
            cls.recalculate_balance(material.id)
    def recalculate_own_balance(self):
        """Пересчитывает баланс для текущего материала"""
        return self.recalculate_balance(self.id)
    @classmethod
    def update_all_reserved_quantities(cls):
        """Пересчитывает резервы для всех материалов на основе активных заказов"""
        from orders.models import OrderItem
        for material in cls.objects.all():
            total_reserved = OrderItem.objects.filter(
                material=material
            ).aggregate(total=Sum('quantity'))['total'] or 0

            # Обновляем только если значение изменилось
            if material.reserved != total_reserved:
                material.reserved = total_reserved
                material.save(update_fields=['reserved'])

    @property
    def availability_status(self):
        """Возвращает статус доступности для цветового отображения"""
        if self.balance == 0 or self.available <= 0:
            return 'red'
        availability_ratio = self.available / self.balance
        return 'green' if availability_ratio >= 0.2 else 'yellow'

    @property
    def available(self):
        """Автоматически рассчитываемое количество ДОСТУПНО"""
        return max(0, self.balance - self.reserved)

    def clean(self):
        """Расчёт НЕХВАТКА"""
        # Всегда пересчитываем нехватку
        self.lack = max(0, self.reserved - self.balance)

    def update_reserved_quantity(self):
        """
        АКТУАЛИЗАЦИЯ: Пересчитывает резерв для конкретного материала
        """
        from orders.models import OrderItem
        from django.db.models import Sum

        total_reserved = OrderItem.objects.filter(
            material=self
        ).aggregate(total=Sum('quantity'))['total'] or 0

        if self.reserved != total_reserved:
            self.reserved = total_reserved
            self.save(update_fields=['reserved'])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = transliterate_slugify(self.name)
        self.lack = max(0, self.reserved - self.balance)
        self.full_clean()  # Вызывает clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mebel:material_detail',
                       args=[self.id, self.slug])


class MaterialOperation(models.Model):
    OPERATION_TYPES = [
        ('write_off', 'Списание'),
        ('receipt', 'Поступление'),
    ]

    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.get_operation_type_display()} {self.quantity} шт. - {self.material.name}"

    def get_edit_url(self):
        return reverse('mebel:operation_edit', args=[self.id])

    def get_absolute_url(self):
        return reverse('mebel:operations_list') + f'?operation={self.id}'

    def can_edit(self):
        """Проверяет, можно ли редактировать операцию (только сегодняшние)"""
        return self.created.date() == timezone.now().date()

