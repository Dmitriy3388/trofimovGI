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
    """
    Динамическая форма для списания материалов.
    Создает поле для каждого материала в заказе.
    """

    def __init__(self, *args, **kwargs):
        order_items = kwargs.pop('order_items')
        super().__init__(*args, **kwargs)

        for item in order_items:
            field_name = f'material_{item.id}'
            self.fields[field_name] = forms.IntegerField(
                label=f'{item.material.name} (Макс.: {item.quantity})',
                min_value=0,
                max_value=item.quantity,  # Нельзя списать больше, чем зарезервировано в этом заказе
                initial=0,
                required=False,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'data-material-id': item.material.id,
                    'data-reserved': item.quantity,
                    'data-balance': item.material.balance
                })
            )
            self.fields[field_name].material_data = {
                'material_id': item.material.id,
                'reserved': item.quantity,
                'balance': item.material.balance
            }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_name', 'customer_name', 'address', 'transferred_amount', 'discount', 'category', 'blueprint', 'visualization']
        widgets = {
            'order_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'transferred_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'blueprint': forms.FileInput(attrs={'class': 'form-control'}),
            'visualization': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'order_name': 'Название',
            'customer_name': 'Имя заказчика',
            'address': 'Адрес',
            'transferred_amount': 'Перечисленные средства',
            'discount': 'Скидка (%)',
            'category': 'Категория',
            'blueprint': 'Чертеж',
            'visualization': 'Визуализация',
        }
