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
from django.http import JsonResponse, HttpResponseBadRequest  # Добавить импорт
from orders.models import Order
from warehouse.utils import managers_required, mto_required
from .forms import MaterialEditForm, MaterialCreateForm  # Добавить импорт
from .models import Material
import json
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from transliterate import slugify as transliterate_slugify
from django.core.paginator import Paginator
from django.db.models import F, ExpressionWrapper, IntegerField
from django.shortcuts import get_object_or_404
from .models import Category, Material, Supplier  # добавляем Supplier
from .forms import MaterialEditForm, MaterialCreateForm, SupplierCreateForm  # добавляем SupplierCreateForm
from django.http import JsonResponse
from django.template.loader import render_to_string


# остальные импорты...

# НОВЫЙ VIEW ДЛЯ СОЗДАНИЯ ПОСТАВЩИКА ЧЕРЕЗ МОДАЛКУ
@login_required
@require_http_methods(["GET", "POST"])
def supplier_create_modal(request):
    if request.method == 'POST':
        form = SupplierCreateForm(request.POST)
        if form.is_valid():
            supplier = form.save()

            # Если это AJAX запрос, возвращаем JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'message': 'Поставщик успешно создан!'
                })

            # Для не-AJAX запроса определяем, откуда пришел запрос
            referer = request.POST.get('referer') or request.META.get('HTTP_REFERER')

            messages.success(request, f'Поставщик "{supplier.name}" успешно создан!')

            # Пытаемся вернуться на предыдущую страницу
            if referer:
                return redirect(referer)
            else:
                # Если referer нет, возвращаемся к списку материалов
                return redirect('mebel:material_list')

        # Обработка невалидной формы для AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
        # Для не-AJAX просто показываем форму с ошибками
        # (этот случай маловероятен, но на всякий случай)

    else:
        form = SupplierCreateForm()

    # Рендерим форму для модального окна (AJAX)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('mebel/includes/supplier_modal_form.html', {
            'form': form
        }, request=request)
        return JsonResponse({'html': html})

    # Не-AJAX GET запрос (редкий случай)
    return render(request, 'mebel/supplier/create.html', {'form': form})

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

    # Проверяем, является ли запрос AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'dates': dates,
            'counts': counts,
            'has_data': len(dates) > 0,
            'period': period
        }
        return JsonResponse(data)  # Возвращаем JSON для AJAX

    # Конвертируем данные в JSON для безопасной передачи в JavaScript
    dates_json = mark_safe(json.dumps(dates))
    counts_json = mark_safe(json.dumps(counts))

    # Материалы с текущей нехваткой
    current_shortage = Material.objects.filter(lack__gt=0)

    # Материалы с прогнозируемой нехваткой
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
        'has_data': len(dates) > 0
    })


@mto_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialCreateForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            # Генерируем slug, если он не был создан автоматически
            if not material.slug:
                material.slug = transliterate_slugify(material.name)
            material.save()
            messages.success(request, f'Материал "{material.name}" успешно создан!')
            return redirect('mebel:material_detail', id=material.id, slug=material.slug)
    else:
        form = MaterialCreateForm()

    return render(request, 'mebel/material/create.html', {'form': form})


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





@mto_required
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


@mto_required
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
    paginate_by = 15

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
        sort_by = self.request.GET.get('sort', 'name')
        order = self.request.GET.get('order', 'asc')

        queryset = Material.objects.annotate(
            calculated_available=ExpressionWrapper(
                F('balance') - F('reserved'),
                output_field=IntegerField()
            )
        )

        # Добавляем поддержку сортировки по поставщику
        if sort_by == 'supplier':
            # Сортируем по имени поставщика
            if order == 'asc':
                queryset = queryset.order_by('supplier__name')
            else:
                queryset = queryset.order_by('-supplier__name')
        else:
            # Для других полей используем старую логику
            if sort_by == 'available':
                sort_by = 'calculated_available'

            if order == 'asc':
                order_by = sort_by
            else:
                order_by = f'-{sort_by}'

            queryset = queryset.order_by(order_by)

        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            return queryset.filter(category=self.category)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['category'] = getattr(self, 'category', None)

        # Добавляем параметры сортировки в контекст
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['current_order'] = self.request.GET.get('order', 'asc')

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



@mto_required
def material_edit(request, material_id):
    material = get_object_or_404(Material, id=material_id)

    if request.method == 'POST':
        form = MaterialEditForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Материал "{material.name}" успешно обновлен!')
            return redirect('mebel:material_detail', id=material.id, slug=material.slug)
    else:
        form = MaterialEditForm(instance=material)

    return render(request, 'mebel/material/edit.html', {
        'form': form,
        'material': material
    })