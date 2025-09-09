from django.shortcuts import get_object_or_404
from .models import Category, Material
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from .models import MaterialOperation  # Добавьте импорт
from django import forms
from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from datetime import datetime, timedelta
from orders.models import Order
from .models import Material
import json
from django.utils.safestring import mark_safe


@require_POST  # Разрешаем только POST-запросы
@login_required
def refresh_materials(request):
    """Отдельный view только для обновления данных"""
    try:
        # После рефакторинга сигналов эта строка может не понадобиться!
        # Material.update_all_reserved_quantities()
        messages.success(request, '✅ Данные материалов успешно обновлены!')
    except Exception as e:
        messages.error(request, f'❌ Ошибка при обновлении: {e}')

    # Возвращаем на предыдущую страницу
    return redirect(request.META.get('HTTP_REFERER', 'mebel:material_list'))


@login_required
def main_dashboard(request):
    # Данные для графика заказов
    period = request.GET.get('period', 'month')  # week, month, year

    today = datetime.now().date()
    if period == 'week':
        start_date = today - timedelta(days=7)
        trunc_func = TruncDate('created')
    elif period == 'month':
        start_date = today - timedelta(days=30)
        trunc_func = TruncDate('created')
    else:  # year
        start_date = today - timedelta(days=365)
        trunc_func = TruncMonth('created')

    # Получаем данные для графика
    orders_data = Order.objects.filter(
        created__date__gte=start_date
    ).annotate(
        period_field=trunc_func
    ).values('period_field').annotate(
        count=Count('id')
    ).order_by('period_field')

    # Подготавливаем данные для графика
    dates = []
    counts = []

    for item in orders_data:
        if period == 'year':
            dates.append(item['period_field'].strftime('%Y-%m'))
        else:
            dates.append(item['period_field'].strftime('%Y-%m-%d'))
        counts.append(item['count'])

    # Конвертируем данные в JSON для безопасной передачи в JavaScript
    dates_json = mark_safe(json.dumps(dates))
    counts_json = mark_safe(json.dumps(counts))

    # Материалы с текущей нехваткой
    current_shortage = Material.objects.filter(lack__gt=0)

    # Материалы с прогнозируемой нехваткой (баланс меньше 110% от зарезервированного)
    predicted_shortage = Material.objects.filter(
        Q(balance__gt=0) &
        Q(balance__lt=F('reserved') * 1.1) &
        Q(lack=0)
    )

    return render(request, 'mebel/main_dashboard.html', {
        'dates_json': dates_json,
        'counts_json': counts_json,
        'current_shortage': current_shortage,
        'predicted_shortage': predicted_shortage,
        'period': period,
        'has_data': len(dates) > 0  # Флаг наличия данных
    })

@login_required
def material_list(request, category_slug=None):
    """Только отображение данных, без обработки форм"""

    # ТОЛЬКО GET-логика
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





# Форма для списания
class MaterialWriteOffForm(forms.Form):
    quantity = forms.IntegerField(
        label='Количество для списания',
        min_value=1,
        max_value=10000,  # Установим максимальное значение
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите количество',
            'max': 10000  # HTML5 валидация
        })
    )
    reason = forms.CharField(
        label='Причина списания',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Например: брак, порча, производственные потери'
        })
    )

    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        super().__init__(*args, **kwargs)
        if self.material:
            # Динамически устанавливаем максимальное значение
            self.fields['quantity'].widget.attrs['max'] = self.material.balance


# Форма для поступления
class MaterialReceiptForm(forms.Form):
    quantity = forms.IntegerField(
        label='Количество для поступления',
        min_value=1,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите количество'
        })
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Например: закупка, возврат, инвентаризация'
        })
    )


from django.http import JsonResponse, HttpResponseBadRequest  # Добавить импорт


@login_required
@require_http_methods(["GET", "POST"])
def material_write_off(request, material_id):
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        form = MaterialWriteOffForm(request.POST, material=material)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            # Списание
            material.balance -= quantity
            material.save()

            # Сохраняем в лог
            MaterialOperation.objects.create(
                material=material,
                operation_type='write_off',
                quantity=quantity,
                notes=reason,
                user=request.user
            )

            messages.success(request, f'Списано {quantity} единиц материала "{material.name}"')
            return redirect('mebel:material_detail', id=material.id, slug=material.slug)
    else:
        form = MaterialWriteOffForm(material=material)

    return render(request, 'mebel/material/write_off_modal.html', {
        'material': material,
        'form': form,
    })


@login_required
@require_http_methods(["GET", "POST"])
def material_receipt(request, material_id):
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        form = MaterialReceiptForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            comment = form.cleaned_data['comment']

            # Поступление
            material.balance += quantity
            material.save()

            # Сохраняем в лог
            MaterialOperation.objects.create(
                material=material,
                operation_type='receipt',
                quantity=quantity,
                notes=comment,
                user=request.user
            )

            messages.success(request, f'Поступило {quantity} единиц материала "{material.name}"')
            return redirect('mebel:material_detail', id=material.id, slug=material.slug)
    else:
        form = MaterialReceiptForm()

    return render(request, 'mebel/material/receipt_modal.html', {
        'material': material,
        'form': form,
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

class MaterialOperationForm(forms.Form):
    """Базовая форма для операций с материалами"""
    quantity = forms.IntegerField(
        min_value=1,
        label='Количество',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите количество'
        })
    )
    notes = forms.CharField(
        required=False,
        label='Примечания',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительная информация...'
        })
    )


@login_required
def material_detail(request, id, slug):
    material = get_object_or_404(Material, id=id, slug=slug)
    operations = material.operations.all()[:10]  # Последние 10 операций

    context = {
        'material': material,
        'operations': operations,
    }

    return render(request, 'mebel/material/detail.html', context)

