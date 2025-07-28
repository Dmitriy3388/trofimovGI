from django.db import models
from django.urls import reverse
from django.core.validators import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200,
                            unique=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
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
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to='materials/%Y/%m/%d',
                              blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
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

    def save(self, *args, **kwargs):
        """Переопределённое сохранение с автоматическим расчётом"""
        self.full_clean()  # Вызывает clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mebel:material_detail',
                       args=[self.id, self.slug])
