from django.shortcuts import render, get_object_or_404
#from cart.forms import CartAddProductForm
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
    #cart_product_form = CartAddProductForm()
    return render(request,
                  'mebel/material/detail.html',
                  {'product': material})
                   #'cart_product_form': cart_product_form})
