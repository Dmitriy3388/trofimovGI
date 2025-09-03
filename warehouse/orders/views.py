from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from .models import OrderItem, Order
from .forms import OrderForm, OrderItemFormSet, WriteOffForm
from mebel.models import Material
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django import forms


@login_required
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
                    # Проверяем, чтобы списывали не больше чем зарезервировано в ЭТОМ заказе
                    # и не больше чем есть на складе
                    quantity_to_write_off = min(
                        quantity_to_write_off,
                        item.quantity,  # Зарезервировано для этого заказа
                        material.balance  # Общее количество на складе
                    )

                    # Вычитаем списанное количество из общего баланса
                    material.balance -= quantity_to_write_off
                    # Уменьшаем количество, зарезервированное этим заказом
                    item.quantity -= quantity_to_write_off
                    # Увеличиваем счетчик списанного количества
                    item.written_off += quantity_to_write_off
                    # Сохраняем изменения
                    material.save()
                    item.save()

            messages.success(request, 'Материалы успешно списаны со склада.')
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = WriteOffForm(order_items=order_items)

    return render(request, 'orders/order/write_off_modal.html', {
        'order': order,
        'form': form,
    })

@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created')
    paginator = Paginator(orders, 10)  # 10 заказов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'orders/order/list.html', {'page_obj': page_obj})

@login_required
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
                    material.reserved += quantity  # Увеличиваем зарезервированное количество
                    material.save()
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


@staff_member_required
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