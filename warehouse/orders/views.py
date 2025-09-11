from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from .models import OrderItem, Order
from .forms import OrderForm, OrderItemForm, WriteOffForm
from mebel.models import Material
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem
from .forms import OrderItemForm
from django.db.models import Sum, F
from django.db import transaction
from collections import defaultdict
from django.utils import timezone
from django.utils import timezone
from datetime import datetime
from warehouse.utils import managers_required, mto_required
import dateutil.parser
from django.db.models import Count
import json
from django.utils.safestring import mark_safe

# Добавьте это в начале файла, после импортов
OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    fields=['material', 'quantity']
)

@mto_required
@require_http_methods(["GET", "POST"])
def order_write_off(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all().select_related('material')

    if request.method == 'POST':
        form = WriteOffForm(request.POST, order_items=order_items)
        if form.is_valid():
            for item in order_items:
                field_name = f'material_{item.id}'
                quantity_to_write_off = form.cleaned_data.get(field_name, 0)

                if quantity_to_write_off > 0:
                    material = item.material
                    # Проверяем, чтобы списывали не больше чем зарезервировано
                    quantity_to_write_off = min(
                        quantity_to_write_off,
                        item.quantity,
                        material.balance
                    )

                    # Вычитаем списанное количество
                    material.balance -= quantity_to_write_off
                    item.quantity -= quantity_to_write_off
                    item.written_off += quantity_to_write_off

                    # Добавляем операцию в историю
                    notes = form.cleaned_data.get('notes', '')
                    item.add_operation_to_history(
                        'write_off',
                        quantity_to_write_off,
                        request.user,
                        notes
                    )

                    # Сохраняем изменения
                    material.save()
                    item.save()

            messages.success(request, 'Материалы успешно списаны со склада.')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = WriteOffForm(order_items=order_items)

    # Получаем историю операций для отображения
    operation_history = []
    for item in order_items:
        for op in item.operation_history:
            # Преобразуем строку в datetime объект
            timestamp = op.get('timestamp')
            if isinstance(timestamp, str):
                try:
                    timestamp = dateutil.parser.isoparse(timestamp)
                except (ValueError, TypeError):
                    timestamp = None

            operation_history.append({
                'material': item.material.name,
                'type': op.get('type', ''),
                'quantity': op.get('quantity', 0),
                'user': op.get('user', ''),
                'timestamp': timestamp,  # ← Теперь это datetime объект
                'notes': op.get('notes', '')
            })

    # Сортируем по времени (новые сверху)
    operation_history.sort(key=lambda x: x['timestamp'] or timezone.now(), reverse=True)

    return render(request, 'orders/order/write_off_modal.html', {
        'order': order,
        'form': form,
        'operation_history': operation_history[:10]  # Последние 10 операций
    })


@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Данные для графика
    status_stats = Order.objects.values('paid').annotate(count=Count('id')).order_by('paid')

    status_labels = []
    status_data = []
    background_colors = []
    border_colors = []

    # Цвета для каждого статуса
    color_map = {
        'not_paid': ('rgba(255, 99, 132, 0.2)', 'rgba(255, 99, 132, 1)'),
        'partially_paid': ('rgba(54, 162, 235, 0.2)', 'rgba(54, 162, 235, 1)'),
        'fully_paid': ('rgba(75, 192, 192, 0.2)', 'rgba(75, 192, 192, 1)')
    }

    for stat in status_stats:
        status_label = dict(Order.PaymentStatus.choices).get(stat['paid'])
        status_labels.append(status_label)
        status_data.append(stat['count'])

        # Получаем цвета из color_map
        bg_color, border_color = color_map.get(stat['paid'], ('rgba(0, 0, 0, 0.2)', 'rgba(0, 0, 0, 1)'))
        background_colors.append(bg_color)
        border_colors.append(border_color)

    # Конвертируем в JSON
    status_labels_json = mark_safe(json.dumps(status_labels))
    status_data_json = mark_safe(json.dumps(status_data))
    background_colors_json = mark_safe(json.dumps(background_colors))
    border_colors_json = mark_safe(json.dumps(border_colors))

    return render(request, 'orders/order/list.html', {
        'page_obj': page_obj,
        'status_labels_json': status_labels_json,
        'status_data_json': status_data_json,
        'background_colors_json': background_colors_json,
        'border_colors_json': border_colors_json
    })

@managers_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            order = form.save()
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    material = item_form.cleaned_data['material']
                    quantity = item_form.cleaned_data['quantity']
                    #material.reserved += quantity  # Увеличиваем зарезервированное количество
                    #material.save()
                    OrderItem.objects.create(
                        order=order,
                        material=item_form.cleaned_data['material'],
                        quantity=item_form.cleaned_data['quantity'],
                        price=item_form.cleaned_data['material'].price
                    )
            return redirect('orders:order_detail', order.id)
    else:
        form = OrderForm()
        formset = OrderItemFormSet(prefix='items')

    return render(request, 'orders/order/create.html', {
        'form': form,
        'formset': formset,
        'total_price': 0.00,
        'materials': Material.objects.all()
    })

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request,'admin/orders/order/detail.html',{'order': order})
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order/detail.html', {
        'order': order,
    })


@managers_required
@require_http_methods(["GET", "POST"])
def order_edit(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Создаем inline formset factory
    OrderItemFormSet = inlineformset_factory(
        Order,
        OrderItem,
        form=OrderItemForm,
        extra=1,
        can_delete=True,
        fields=['material', 'quantity']
    )

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                # Сохраняем основную информацию заказа
                order = form.save(commit=False)

                # Используем транзакцию для обеспечения целостности данных
                with transaction.atomic():
                    order.save()

                    # Создаем словарь для агрегации данных по материалам
                    materials_dict = defaultdict(lambda: {
                        'quantity': 0,
                        'written_off': 0,
                        'operation_history': []
                    })

                    # Собираем данные из форм
                    for form_in_formset in formset:
                        if form_in_formset.cleaned_data and not form_in_formset.cleaned_data.get('DELETE', False):
                            material = form_in_formset.cleaned_data['material']
                            quantity = form_in_formset.cleaned_data['quantity']

                            # Если материал уже есть в словаре, суммируем значения
                            if material.id in materials_dict:
                                materials_dict[material.id]['quantity'] += quantity
                                # Для существующих записей сохраняем историю операций
                                if form_in_formset.instance.pk:
                                    materials_dict[material.id]['written_off'] = form_in_formset.instance.written_off
                                    materials_dict[material.id][
                                        'operation_history'] = form_in_formset.instance.operation_history
                            else:
                                # Для новых материалов используем переданные значения
                                materials_dict[material.id] = {
                                    'quantity': quantity,
                                    'written_off': form_in_formset.instance.written_off if form_in_formset.instance.pk else 0,
                                    'operation_history': form_in_formset.instance.operation_history if form_in_formset.instance.pk else []
                                }

                    # Удаляем все существующие элементы заказа
                    OrderItem.objects.filter(order=order).delete()

                    # Создаем новые элементы заказа с агрегированными данными
                    for material_id, data in materials_dict.items():
                        material = Material.objects.get(id=material_id)
                        OrderItem.objects.create(
                            order=order,
                            material=material,
                            quantity=data['quantity'],
                            price=material.price,
                            written_off=data['written_off'],
                            operation_history=data['operation_history']
                        )

                    # Обновляем резерв материалов
                    for material_id in materials_dict:
                        material = Material.objects.get(id=material_id)
                        material.update_reserved_quantity()

                messages.success(request, 'Заказ успешно обновлен.')
                return redirect('orders:order_detail', order_id=order.id)

            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {e}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order, prefix='items')

    return render(request, 'orders/order/edit.html', {
        'form': form,
        'formset': formset,
        'order': order,
    })

@login_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html',
                            {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response,
        stylesheets=[weasyprint.CSS(
            settings.STATIC_ROOT / 'css/pdf.css')])
    return response