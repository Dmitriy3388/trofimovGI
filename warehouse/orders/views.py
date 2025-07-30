from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from .models import OrderItem, Order
from .forms import OrderCreateForm
from .tasks import order_created
from ordercart.ordercart import OrderCart
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'orders/order/list.html', {'page_obj': page_obj})

@login_required()
def order_create(request):
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            selected_materials = form.cleaned_data['materials']
            for material in selected_materials:
                OrderItem.objects.create(
                    order=order,
                    material=material,
                    price=material.price,
                    quantity=1
                )
            return redirect('orders:order_detail', order.id)
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'form': form})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request,'admin/orders/order/detail.html',{'order': order})


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