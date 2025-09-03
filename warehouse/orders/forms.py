from mebel.models import Material
from django import forms
from .models import Order, OrderItem


class OrderItemForm(forms.ModelForm):
    material = forms.ModelChoiceField(queryset=Material.objects.all())
    quantity = forms.IntegerField(min_value=1, initial=1)

    class Meta:
        model = OrderItem
        fields = ['material', 'quantity']


OrderItemFormSet = forms.formset_factory(
    OrderItemForm,
    extra=1,
    can_delete=True
)

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
        fields = ['first_name', 'last_name', 'address', 'city', 'paid']
        widgets = {
            'paid': forms.Select(choices=Order.PaymentStatus.choices),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Можно установить значение по умолчанию
        self.fields['paid'].initial = Order.PaymentStatus.NOT_PAID
