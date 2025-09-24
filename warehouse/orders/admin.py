import csv
import datetime
from django.http import HttpResponse
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)

    # Обновляем поля для экспорта
    fields = [
        field for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
           and field.name not in ['blueprint', 'visualization']  # Исключаем бинарные поля
    ]

    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])

    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)

    return response


class OrderItemInLine(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['material']


def order_detail(obj):
    url = reverse('orders:admin_order_detail', args=[obj.id])
    return mark_safe(f'<a href="{url}">View</a>')


def order_pdf(obj):
    url = reverse('orders:admin_order_pdf', args=[obj.id])
    return mark_safe(f'<a href="{url}">PDF</a>')


order_pdf.short_description = 'Invoice'


def display_blueprint(obj):
    if obj.blueprint:
        return mark_safe(f'<img src="{obj.blueprint.url}" width="100" height="100" />')
    return "Нет чертежа"


def display_visualization(obj):
    if obj.visualization:
        return mark_safe(f'<img src="{obj.visualization.url}" width="100" height="100" />')
    return "Нет визуализации"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Обновляем список отображаемых полей
    list_display = [
        'id', 'order_name', 'customer_name', 'category', 'deadline',
        'address', 'transferred_amount', 'discount',
        'paid', 'created', 'updated',
        order_detail, order_pdf
    ]

    list_filter = ['paid', 'created', 'updated', 'category', 'deadline']

    # Добавляем поиск по названию заказа и имени заказчика
    search_fields = ['order_name', 'customer_name']

    inlines = [OrderItemInLine]
    actions = [export_to_csv]

    # Поля для формы редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('order_name', 'customer_name', 'address',
                       'category', 'discount', 'deadline')
        }),
        ('Финансовая информация', {
            'fields': ('transferred_amount', 'paid')
        }),
        ('Изображения', {
            'fields': ('blueprint', 'visualization', 'display_blueprint', 'display_visualization'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    # Делаем поля только для чтения
    readonly_fields = ['created', 'updated', 'display_blueprint', 'display_visualization']

    # Добавляем вычисляемые поля для отображения изображений
    def display_blueprint(self, obj):
        return display_blueprint(obj)

    display_blueprint.short_description = 'Чертеж'

    def display_visualization(self, obj):
        return display_visualization(obj)

    display_visualization.short_description = 'Визуализация'

    def save_model(self, request, obj, form, change):
        # Сначала сохраняем объект
        super().save_model(request, obj, form, change)
        # Затем обновляем статус оплаты
        obj.update_payment_status()
        obj.save(update_fields=['paid'])

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # После сохранения связанных объектов обновляем статус оплаты
        form.instance.update_payment_status()
        form.instance.save(update_fields=['paid'])


# Обновляем описание для экспорта
export_to_csv.short_description = 'Export to CSV'