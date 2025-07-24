from django import forms
from .models import Order
from django import forms
from mebel.models import Material

class OrderCreateForm(forms.ModelForm):
    materials = forms.ModelMultipleChoiceField(
        queryset=Material.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False
    )

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'address', 'postal_code', 'city', 'materials']

