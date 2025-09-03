from django.shortcuts import render, get_object_or_404
from .models import Category, Material
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect


@login_required
def main_dashboard(request):
    return render(request, 'mebel/main_dashboard.html')


@login_required
def material_list(request, category_slug=None):
    # Обрабатываем запрос на обновление данных
    if request.method == 'POST' and 'refresh_data' in request.POST:
        try:
            Material.update_all_reserved_quantities()
            messages.success(request, '✅ Данные материалов успешно обновлены!')
        except Exception as e:
            messages.error(request, f'❌ Ошибка при обновлении: {e}')

        # ПРАВИЛЬНЫЙ редирект
        if category_slug:
            return redirect('mebel:material_list_by_category', category_slug=category_slug)
        else:
            return redirect('mebel:material_list')

    # Остальной код без изменений
    sort_by = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')

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

    def post(self, request, *args, **kwargs):
        """Обработка кнопки обновления"""
        if 'refresh_data' in request.POST:
            try:
                Material.update_all_reserved_quantities()
                messages.success(request, '✅ Данные материалов успешно обновлены!')
            except Exception as e:
                messages.error(request, f'❌ Ошибка при обновлении: {e}')

        # Возвращаемся к GET-обработке
        return self.get(request, *args, **kwargs)

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


