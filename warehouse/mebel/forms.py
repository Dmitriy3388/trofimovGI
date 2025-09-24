from django import forms
from .models import Material, Category
from django.core.exceptions import ValidationError
from .models import Material
from django.db.models.functions import Lower, Replace
from django.db.models import Value
from django import forms
from .models import Material, MaterialOperation, Category, Supplier  # добавляем Supplier
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower, Replace
from django.db.models import Value

# НОВАЯ ФОРМА ДЛЯ ПОСТАВЩИКА
class SupplierCreateForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО контактного лица'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Полный адрес'}),
        }
        labels = {
            'name': 'Название поставщика*',
            'contact_person': 'Контактное лицо',
            'phone': 'Телефон',
            'email': 'Email',
            'address': 'Адрес',
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Supplier.objects.filter(name__iexact=name).exists():
            raise ValidationError('Поставщик с таким названием уже существует.')
        return name

class MaterialEditForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'supplier', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control', 'id': 'supplier-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название',
            'category': 'Категория',
            'supplier': 'Поставщик',
            'description': 'Описание',
            'price': 'Цена',
            'image': 'Изображение',
        }


class MaterialOperationEditForm(forms.ModelForm):
    class Meta:
        model = MaterialOperation
        fields = ['quantity', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']

        # Для списания проверяем, чтобы не уйти в отрицательный баланс
        if (self.material and
                self.instance.operation_type == 'write_off' and
                hasattr(self.instance, 'id')):

            # Рассчитываем, каким будет баланс после изменения
            current_balance = self.material.balance

            # Находим разницу между старым и новым количеством списания
            quantity_diff = quantity - self.instance.quantity

            # Предполагаемый новый баланс
            projected_balance = current_balance - quantity_diff

            if projected_balance < 0:
                raise ValidationError(
                    f'Нельзя списать {quantity} шт. Это приведет к отрицательному балансу ({projected_balance})'
                )

        return quantity



# ОБНОВЛЯЕМ СУЩЕСТВУЮЩИЕ ФОРМЫ
class MaterialCreateForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'supplier', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control', 'id': 'supplier-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Название',
            'category': 'Категория',
            'supplier': 'Поставщик',
            'description': 'Описание',
            'price': 'Цена',
            'image': 'Изображение',
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        normalized_name = name.lower().replace(' ', '')
        if Material.objects.annotate(
            normalized_name=Lower(Replace('name', Value(' '), Value('')))
        ).filter(normalized_name=normalized_name).exists():
            raise ValidationError('Материал с таким названием уже существует.')
        return name