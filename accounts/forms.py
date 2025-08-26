from typing import Any
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.password_validation import validate_password

class CreateUserForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)  # Adicione este campo para a confirmação da senha

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        if username and ' ' in username:
            self.add_error('username', ValidationError("Username cannot contain spaces."))
        cleaned_data['username'] = username.lower()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            self.add_error('password2', ValidationError("The two password fields didn't match."))
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if username and password:
            # Try to find user by email first
            try:
                user = User.objects.get(email=username)
                # If found by email, authenticate with the user's username
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                # If not found by email, try username directly
                user = authenticate(username=username, password=password)
            
            if not user:
                self.add_error(None, ValidationError("Invalid username or password."))
        else:
            self.add_error(None, ValidationError("Both fields are required."))
        return cleaned_data

class CustomPasswordResetForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, label="New Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
            try:
                validate_password(password1)
            except forms.ValidationError as e:
                self.add_error("password1", e)

        return cleaned_data