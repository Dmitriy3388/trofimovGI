from django.contrib import admin
from .models import Category, Material


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Material)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'available', 'balance', 'reserved', 'lack', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'lack', 'category']
    prepopulated_fields = {'slug': ('name',)}

# Register your models here.
