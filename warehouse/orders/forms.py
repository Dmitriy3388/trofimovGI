from django import forms
from .models import Order
from django import forms
from mebel.models import Material
from .models import OrderItem
from django import forms
from django.contrib.admin.widgets import AdminTextInputWidget, AdminIntegerFieldWidget
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


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'address', 'city']
