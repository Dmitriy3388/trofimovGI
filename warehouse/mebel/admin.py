from django.contrib import admin
from .models import Category, Material, Supplier  # добавляем импорт Supplier
from django.utils.html import format_html

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'created']
    list_filter = ['created']
    search_fields = ['name', 'contact_person', 'phone']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    # Добавляем supplier в list_display
    list_display = ['name', 'supplier', 'balance', 'reserved',
                   'available_with_status', 'lack', 'updated']
    list_filter = ['created', 'updated', 'lack', 'category', 'supplier']  # добавляем supplier в фильтры
    # Добавляем поиск по поставщику
    search_fields = ['name', 'supplier__name']

    def available_with_status(self, obj):
        """Цветное отображение с иконками"""
        colors = {
            'green': '#4CAF50',
            'yellow': '#FFC107',
            'red': '#F44336'
        }

        icons = {
            'green': '🟢',
            'yellow': '⚠️',
            'red': '❌'
        }

        return format_html(
            '{} <span style="color: white; background: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            icons[obj.availability_status],
            colors[obj.availability_status],
            obj.available
        )

    available_with_status.short_description = 'Доступно'
