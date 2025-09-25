from mebel.models import Material
from django import forms
from .models import Order, OrderItem


class OrderItemForm(forms.ModelForm):
    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'min-width: 200px;'
        })
    )
    quantity = forms.IntegerField(
        min_value=0,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'max-width: 100px;'
        })
    )

    class Meta:
        model = OrderItem
        fields = ['material', 'quantity']


class WriteOffForm(forms.Form):
    def __init__(self, *args, **kwargs):
        order_items = kwargs.pop('order_items')
        super().__init__(*args, **kwargs)

        for item in order_items:
            field_name = f'material_{item.id}'
            # Максимум можно списать остаток (исходное количество минус уже списанное)
            max_value = item.quantity - item.written_off

            self.fields[field_name] = forms.IntegerField(
                label=f'{item.material.name} (Макс.: {max_value})',
                min_value=0,
                max_value=max_value,  # ← Исправлено!
                initial=0,
                required=False,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'data-material-id': item.material.id,
                    'data-reserved': max_value,  # ← Обновляем для отображения
                    'data-balance': item.material.balance
                })
            )
            self.fields[field_name].material_data = {
                'material_id': item.material.id,
                'reserved': max_value,  # ← Обновляем
                'balance': item.material.balance
            }

from mebel.models import Material
from django import forms
from .models import Order, OrderItem
from django.utils import timezone
from datetime import timedelta

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_name', 'customer_name', 'address', 'transferred_amount',
                 'discount', 'category', 'deadline', 'blueprint', 'visualization',
                  'installation_status', 'installation_photo'
                  ]
        widgets = {
            'order_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'transferred_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'min': timezone.now().date().isoformat()  # Нельзя выбрать прошедшие даты
                }
            ),
            'blueprint': forms.FileInput(attrs={'class': 'form-control'}),
            'visualization': forms.FileInput(attrs={'class': 'form-control'}),
            'installation_status': forms.Select(attrs={'class': 'form-select'}),
            'installation_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'order_name': 'Название',
            'customer_name': 'Имя заказчика',
            'address': 'Адрес',
            'transferred_amount': 'Перечисленные средства',
            'discount': 'Скидка (%)',
            'category': 'Категория',
            'deadline': 'Дата сдачи',
            'blueprint': 'Чертеж',
            'visualization': 'Визуализация',
            'installation_status': 'Установка',
            'installation_photo': 'Фотография заказа'
        }
