from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from .models import OrderItem, Order
from .forms import OrderForm, OrderItemFormSet
from .tasks import order_created
from ordercart.ordercart import OrderCart
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


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