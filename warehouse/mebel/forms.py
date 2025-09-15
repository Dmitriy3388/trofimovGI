from django import forms
from .models import Material, Category
from django.core.exceptions import ValidationError
from .models import Material
from django.db.models.functions import Lower, Replace
from django.db.models import Value

class MaterialEditForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }





class MaterialCreateForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'description', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        # Нормализуем название: приводим к нижнему регистру и удаляем пробелы
        normalized_name = name.lower().replace(' ', '')

        # Проверяем, существует ли материал с таким нормализованным названием
        if Material.objects.annotate(
                normalized_name=Lower(Replace('name', Value(' '), Value('')))
        ).filter(normalized_name=normalized_name).exists():
            raise ValidationError('Материал с таким названием уже существует.')

        return name