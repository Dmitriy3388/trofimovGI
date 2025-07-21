from django import forms


MATERIAL_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]


class OrderCartAddMaterialForm(forms.Form):
    """
    Форма добавления материала к заказу
    """
    quantity = forms.TypedChoiceField(
                                choices=MATERIAL_QUANTITY_CHOICES,
                                coerce=int)
    override = forms.BooleanField(required=False,
                                  initial=False,
                                  widget=forms.HiddenInput)
