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

# Добавим в views.py после существующих импортов
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta

# Добавим в views.py
from django.db.models import Sum
from datetime import datetime, timedelta
import json

from django.core.paginator import Paginator
from .forms import MaterialOperationEditForm


@login_required
@mto_required
def operations_list(request):
    """Список всех операций с фильтрацией"""
    operations = MaterialOperation.objects.select_related(
        'material', 'user'
    ).order_by('-created')

    # Фильтрация
    operation_type = request.GET.get('type', '')
    material_id = request.GET.get('material', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if operation_type:
        operations = operations.filter(operation_type=operation_type)

    if material_id:
        operations = operations.filter(material_id=material_id)

    if date_from:
        operations = operations.filter(created__date__gte=date_from)

    if date_to:
        operations = operations.filter(created__date__lte=date_to)

    # Пагинация
    paginator = Paginator(operations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Материалы для фильтра
    materials = Material.objects.all()

    context = {
        'page_obj': page_obj,
        'materials': materials,
        'operation_type': operation_type,
        'selected_material': material_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'mebel/operations/operations_list.html', context)


@login_required
@mto_required
def operation_edit(request, operation_id):
    """Редактирование операции - УПРОЩЕННАЯ ВЕРСИЯ"""
    operation = get_object_or_404(MaterialOperation, id=operation_id)
    material = operation.material

    # Сохраняем исходный баланс для сообщения
    original_balance = material.balance

    if request.method == 'POST':
        form = MaterialOperationEditForm(
            request.POST,
            instance=operation,
            material=material
        )

        if form.is_valid():
            # Просто сохраняем операцию
            operation = form.save()

            # Пересчитываем баланс материала на основе ВСЕХ операций
            Material.recalculate_balance(material.id)

            # Обновляем объект material
            material.refresh_from_db()

            messages.success(request,
                             f'Операция #{operation.id} успешно отредактирована. ' +
                             f'Баланс пересчитан: {original_balance} → {material.balance}')
            return redirect('mebel:operations_list')
    else:
        form = MaterialOperationEditForm(instance=operation, material=material)

    return render(request, 'mebel/operations/operation_edit.html', {
        'form': form,
        'operation': operation,
        'material': material
    })


@login_required
@mto_required
def operation_detail(request, operation_id):
    """Детальная информация об операции"""
    operation = get_object_or_404(MaterialOperation, id=operation_id)

    return render(request, 'mebel/operations/operation_detail.html', {
        'operation': operation
    })


@login_required
@mto_required
def recalculate_balances(request):
    """Принудительный пересчет всех балансов"""
    try:
        Material.recalculate_all_balances()
        messages.success(request, 'Балансы всех материалов успешно пересчитаны')
    except Exception as e:
        messages.error(request, f'Ошибка при пересчете балансов: {e}')

    return redirect('mebel:operations_list')
@login_required
def material_operations(request, material_id):
    """Возвращает детальную информацию об операциях материала"""
    material = get_object_or_404(Material, id=material_id)

    # Операции из MaterialOperation
    operations = MaterialOperation.objects.filter(material=material).order_by('-created')[:50]

    # Резервирования из OrderItem
    from orders.models import OrderItem
    reservations = OrderItem.objects.filter(material=material).order_by('-order__created')[:50]

    operations_data = []

    for op in operations:
        operations_data.append({
            'date': op.created.isoformat(),
            'type': op.get_operation_type_display(),
            'quantity': op.quantity,
            'notes': op.notes,
            'user': op.user.username if op.user else 'Система',
            'source': 'operation'
        })

    for res in reservations:
        operations_data.append({
            'date': res.order.created.isoformat(),
            'type': 'Резервирование',
            'quantity': res.quantity,
            'notes': f'Заказ #{res.order.id}',
            'user': res.order.user.username if res.order.user else 'Система',
            'source': 'order'
        })

    # Сортируем по дате
    operations_data.sort(key=lambda x: x['date'], reverse=True)

    return JsonResponse(operations_data, safe=False)

@login_required
def material_chart_data(request, material_id):
    """Возвращает данные для графика наличия материала"""
    material = get_object_or_404(Material, id=material_id)

    # Получаем операции за последний год
    one_year_ago = timezone.now() - timedelta(days=365)
    operations = MaterialOperation.objects.filter(
        material=material,
        created__gte=one_year_ago
    ).order_by('created')

    # Также получаем операции из заказов (резервирования)
    from orders.models import OrderItem
    order_operations = OrderItem.objects.filter(
        material=material,
        order__created__gte=one_year_ago
    ).order_by('order__created')

    # Собираем все операции вместе
    all_operations = []

    # Добавляем MaterialOperation
    for op in operations:
        all_operations.append({
            'date': op.created,
            'type': op.operation_type,
            'quantity': op.quantity,
            'source': 'operation'
        })

    # Добавляем OrderItem (резервирования)
    for item in order_operations:
        all_operations.append({
            'date': item.order.created,
            'type': 'reservation',
            'quantity': item.quantity,
            'source': 'order'
        })

    # Сортируем все операции по дате
    all_operations.sort(key=lambda x: x['date'])

    # Создаем временные точки для графика (по месяцам)
    dates = []
    quantities = []

    # Начинаем с текущего баланса и идем назад
    current_date = timezone.now().date()
    start_date = current_date - timedelta(days=365)

    # Создаем точки для каждого месяца
    temp_date = start_date.replace(day=1)  # Начинаем с первого дня месяца
    monthly_data = {}

    while temp_date <= current_date:
        month_key = temp_date.strftime('%Y-%m')
        monthly_data[month_key] = {
            'date': temp_date,
            'receipt': 0,
            'write_off': 0,
            'reservation': 0
        }
        # Переходим к следующему месяцу
        if temp_date.month == 12:
            temp_date = temp_date.replace(year=temp_date.year + 1, month=1)
        else:
            temp_date = temp_date.replace(month=temp_date.month + 1)

    # Распределяем операции по месяцам
    for op in all_operations:
        month_key = op['date'].strftime('%Y-%m')
        if month_key in monthly_data:
            if op['type'] == 'receipt':
                monthly_data[month_key]['receipt'] += op['quantity']
            elif op['type'] == 'write_off':
                monthly_data[month_key]['write_off'] += op['quantity']
            elif op['type'] == 'reservation':
                monthly_data[month_key]['reservation'] += op['quantity']

    # Восстанавливаем историю баланса (идем от текущего значения назад)
    current_balance = material.balance
    balance_history = {current_date.strftime('%Y-%m'): current_balance}

    # Сортируем месяцы в обратном порядке (от текущего к прошлому)
    sorted_months = sorted(monthly_data.keys(), reverse=True)

    for i, month_key in enumerate(sorted_months):
        if month_key == current_date.strftime('%Y-%m'):
            # Текущий месяц - используем текущий баланс
            continue

        # Для предыдущих месяцев: вычитаем поступления и прибавляем списания/резервирования
        # (т.к. идем назад во времени)
        month_data = monthly_data[month_key]
        current_balance = current_balance - month_data['receipt'] + month_data['write_off'] + month_data['reservation']
        balance_history[month_key] = max(0, current_balance)  # Баланс не может быть отрицательным

    # Сортируем данные по дате для графика
    sorted_history = sorted(balance_history.items(), key=lambda x: x[0])

    dates = [item[0] for item in sorted_history]
    quantities = [item[1] for item in sorted_history]

    return JsonResponse({
        'material_name': material.name,
        'dates': dates,
        'quantities': quantities,
        'current_balance': material.balance,
        'current_available': material.available,
        'reserved': material.reserved
    })


@login_required
def material_daily_chart_data(request, material_id):
    """Данные для графика по дням - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    material = get_object_or_404(Material, id=material_id)

    # Получаем операции за ВСЕ время, а не за год
    operations = MaterialOperation.objects.filter(
        material=material
    ).order_by('created')

    # Получаем резервирования за ВСЕ время
    from orders.models import OrderItem
    reservations = OrderItem.objects.filter(
        material=material
    ).order_by('order__created')

    # Собираем ВСЕ события за всю историю материала
    all_events = []

    for op in operations:
        all_events.append({
            'date': op.created,
            'type': op.operation_type,
            'quantity': op.quantity,
            'source': 'operation'
        })

    for res in reservations:
        all_events.append({
            'date': res.order.created,
            'type': 'reservation',
            'quantity': res.quantity,
            'source': 'order'
        })

    # Сортируем по дате (от старых к новым)
    all_events.sort(key=lambda x: x['date'])

    # Восстанавливаем историю баланса ПРАВИЛЬНО
    # Начинаем с ИЗВЕСТНОГО начального баланса (если есть самая первая операция)
    current_balance = 0
    balance_history = []

    # Если есть события, находим баланс ДО первого события
    if all_events:
        # Вычисляем баланс на момент ДО первой операции
        # Для этого идем ОТ ТЕКУЩЕГО баланса НАЗАД через все операции
        temp_balance = material.balance

        # Идем в обратном порядке (от новых к старым) и "отменяем" операции
        for event in reversed(all_events):
            if event['type'] == 'receipt':
                temp_balance -= event['quantity']  # Отменяем поступление
            elif event['type'] == 'write_off':
                temp_balance += event['quantity']  # Отменяем списание
            # Резервирования не влияют на физический баланс

        current_balance = max(0, temp_balance)  # Начальный баланс ДО всех операций

    # Теперь идем вперед по времени и применяем операции
    dates = []
    quantities = []

    # Добавляем начальную точку (если есть история)
    if all_events:
        first_date = all_events[0]['date'].date()
        # Добавляем точку за день до первой операции
        prev_date = first_date - timedelta(days=1)
        dates.append(prev_date.isoformat())
        quantities.append(current_balance)

    # Применяем операции в хронологическом порядке
    for event in all_events:
        event_date = event['date'].date()

        if event['type'] == 'receipt':
            current_balance += event['quantity']
        elif event['type'] == 'write_off':
            current_balance = max(0, current_balance - event['quantity'])  # Не уходим в минус

        # Добавляем точку после операции
        dates.append(event_date.isoformat())
        quantities.append(current_balance)

    # Ограничиваем последним годом для производительности
    one_year_ago = (timezone.now() - timedelta(days=365)).date()

    filtered_data = []
    for i, date_str in enumerate(dates):
        date_obj = datetime.fromisoformat(date_str).date()
        if date_obj >= one_year_ago:
            filtered_data.append((date_str, quantities[i]))

    if filtered_data:
        dates_filtered, quantities_filtered = zip(*filtered_data)
    else:
        dates_filtered, quantities_filtered = [], []

    return JsonResponse({
        'material_name': material.name,
        'dates': dates_filtered,
        'quantities': quantities_filtered,
        'current_balance': material.balance,
        'current_available': material.available,
        'reserved': material.reserved
    })

# View для автодополнения поиска
# Добавим в views.py улучшенную функцию автодополнения
@login_required
def material_autocomplete(request):
    """Автодополнение для поиска материалов"""
    query = request.GET.get('q', '').strip()

    # Логируем запрос для отладки
    print(f"Autocomplete query: '{query}'")

    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    try:
        # Используем более гибкий поиск
        materials = Material.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(supplier__name__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category', 'supplier').distinct()[:10]

        results = []
        for material in materials:
            results.append({
                'id': material.id,
                'name': material.name,
                'category': material.category.name if material.category else 'Без категории',
                'balance': material.balance,
                'supplier': material.supplier.name if material.supplier else 'Не указан'
            })

        print(f"Found {len(results)} materials")
        return JsonResponse(results, safe=False)

    except Exception as e:
        print(f"Error in material_autocomplete: {e}")
        # Возвращаем пустой список при ошибке
        return JsonResponse([], safe=False)


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