from django.shortcuts import render, get_object_or_404
from ordercart.forms import OrderCartAddMaterialForm
from .models import Category, Material
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect


@login_required
def main_dashboard(request):
    return render(request, 'mebel/main_dashboard.html')

@login_required
def material_list(request, category_slug=None):
    sort_by = request.GET.get('sort', 'name')  # По умолчанию сортируем по имени
    order = request.GET.get('order', 'asc')    # По умолчанию порядок возрастающий

    if order == 'asc':
        order_by = sort_by
    else:
        order_by = f'-{sort_by}'
    category = None
    categories = Category.objects.all()
    materials = Material.objects.all().order_by(order_by)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        materials = materials.filter(category=category)
    return render(request,
                  'mebel/material/list.html',
                  {'category': category,
                   'categories': categories,
                   'materials': materials,
                   'current_sort': sort_by,
                   'current_order': order
                   })

class MaterialListView(LoginRequiredMixin, ListView):
    model = Material
    context_object_name = 'materials'
    template_name = 'mebel/material/list.html'
    paginate_by = 3

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            return queryset.filter(category=self.category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['category'] = getattr(self, 'category', None)
        return context

@login_required
def material_detail(request, id, slug):
    material = get_object_or_404(Material, id=id, slug=slug)
    ordercart_material_form = OrderCartAddMaterialForm()
    return render(request,
                  'mebel/material/detail.html',
                  {'material': material, 'ordercart_material_form': ordercart_material_form})
