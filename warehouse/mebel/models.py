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
    available = models.BooleanField(default=True)
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
            models.Index(fields=['-created']),
        ]

    def clean(self):
        if self.reserved > self.balance:
            raise ValidationError("Зарезервировано не может быть больше остатка!")

    def save(self, *args, **kwargs):
        # 1. Обновляем available
        self.available = self.lack == 0
        # 2. Проверяем reserved <= balance и другие валидации
        try:
            self.full_clean()  # Вызовет clean() (если он есть)
            super().save(*args, **kwargs)
        except ValidationError as e:
            raise ValidationError("Ошибка: резерв > остатка")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('mebel:material_detail',
                       args=[self.id, self.slug])
