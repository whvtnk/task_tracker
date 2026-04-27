from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Task, Organization

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assignee', 'priority', 'deadline', 'estimated_hours']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'project': forms.TextInput(attrs={'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PersonalTaskForm(forms.ModelForm):
    """Форма для личных задач пользователя"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('user', 'Обычный пользователь'),
        ('manager', 'Менеджер (создать организацию)'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio'}),
        label='Я хочу'
    )
    organization_name = forms.CharField(
        max_length=100,
        required=False,
        label='Название организации',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название организации'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        org_name = cleaned_data.get('organization_name')
        if role == 'manager' and not org_name:
            raise forms.ValidationError('Менеджер должен указать название организации.')
        return cleaned_data

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название организации'})
        }