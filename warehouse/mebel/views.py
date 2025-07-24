from django.shortcuts import render, get_object_or_404
from ordercart.forms import OrderCartAddMaterialForm
from .models import Category, Material
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


@login_required
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

class MaterialListView(LoginRequiredMixin, ListView):
    model = Material  # Указываем модель
    context_object_name = 'materials'  # Исправляем на множественное число
    template_name = 'mebel/material/list.html'
    paginate_by = 3

    def get_queryset(self):
        # Получаем queryset с фильтрацией по категории
        queryset = super().get_queryset()
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            return queryset.filter(category=self.category)
        self.category = None
        return queryset

    def get_context_data(self, **kwargs):
        # Добавляем категории в контекст
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['category'] = self.category
        return context

@login_required
def material_detail(request, id, slug):
    material = get_object_or_404(Material, id=id, slug=slug)
    ordercart_material_form = OrderCartAddMaterialForm()
    return render(request,
                  'mebel/material/detail.html',
                  {'material': material, 'ordercart_material_form': ordercart_material_form})
