from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from mebel.models import Material
from .ordercart import OrderCart
from .forms import OrderCartAddMaterialForm
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def ordercart_add(request, material_id):
    ordercart = OrderCart(request)
    material = get_object_or_404(Material, id=material_id)
    form = OrderCartAddMaterialForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        ordercart.add(material=material,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
    return redirect('ordercart:ordercart_detail')

@login_required
@require_POST
def ordercart_remove(request, material_id):
    ordercart = OrderCart(request)
    material = get_object_or_404(Material, id=material_id)
    ordercart.remove(material)
    return redirect('ordercart:ordercart_detail')

@login_required
def ordercart_detail(request):
    ordercart = OrderCart(request)
    for item in ordercart:
        item['update_quantity_form'] = OrderCartAddMaterialForm(initial={
                            'quantity': item['quantity'],
                            'override': True})
    return render(request, 'ordercart/detail.html', {'ordercart': ordercart})