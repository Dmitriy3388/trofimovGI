from django import forms
from django.contrib.auth.models import User
from .models import Profile

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'email': 'Email'
        }

    def clean_password2(self):
        cd = self.cleaned_data
        password = cd.get('password')
        password2 = cd.get('password2')

        # Если пароль есть - валидируем его
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                # Переводим сообщения об ошибках на русский
                russian_errors = []
                for error in e.messages:
                    if 'too short' in error.lower():
                        russian_errors.append('Пароль должен содержать минимум 8 символов.')
                    elif 'too common' in error.lower():
                        russian_errors.append('Этот пароль слишком распространен.')
                    elif 'entirely numeric' in error.lower():
                        russian_errors.append('Пароль не может состоять только из цифр.')
                    elif 'too similar' in error.lower():
                        russian_errors.append('Пароль слишком похож на другую личную информацию.')
                    else:
                        russian_errors.append(error)  # Оставляем оригинальное сообщение

                raise forms.ValidationError(russian_errors)

        # Проверяем совпадение паролей
        if password and password2 and password != password2:
            raise forms.ValidationError('Пароли не совпадают.')

        return password2

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email уже используется.')
        return data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('Имя пользователя уже занято.')
        return username
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        data = self.cleaned_data['email']
        qs = User.objects.exclude(id=self.instance.id)\
                         .filter(email=data)
        if qs.exists():
            raise forms.ValidationError('Email already in use.')
        return data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'photo']