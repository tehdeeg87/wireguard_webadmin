from django import forms
from django.utils.translation import gettext_lazy as _

class OrderForm(forms.Form):
    email = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    user_count = forms.IntegerField(
        label=_('Number of Users'),
        min_value=5,
        max_value=254,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number of users (5-254)'})
    ) 