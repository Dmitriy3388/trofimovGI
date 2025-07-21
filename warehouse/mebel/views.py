from django.shortcuts import render, get_object_or_404
from ordercart.forms import OrderCartAddMaterialForm
from .models import Category, Material


def material_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    materials = Material.objects.all()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        materials = materials.filter(category=category)
    return render(request,
                  'mebel/material/list.html',
                  {'category': category,
                   'categories': categories,
                   'materials': materials})


def material_detail(request, id, slug):
    material = get_object_or_404(Material,
                                id=id,
                                slug=slug
                                )
    ordercart_material_form = OrderCartAddMaterialForm()
    return render(request,
                  'mebel/material/detail.html',
                  {'material': material, 'ordercart_material_form': ordercart_material_form})
