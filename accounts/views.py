from django.shortcuts import render, Http404, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from user_manager.forms import UserAclForm
from api.views import get_api_key
from .forms import CreateUserForm, LoginForm, CustomPasswordResetForm
from django.http import HttpResponse
from user_manager.models import UserAcl
from django import forms


def view_create_first_user(request):
    if User.objects.filter().all():
        raise Http404('Superuser already exists')
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            new_user = User.objects.create_superuser(username=username, password=password)
            UserAcl.objects.create(user=new_user, user_level=50)
            return render(request, 'accounts/superuser_created.html')
    else:
        form = CreateUserForm()
    return render(request, 'accounts/create_first_user.html', {'form': form})

@login_required
def view_mgacct(request):
    uuid_str = request.GET.get("uuid")

    if not uuid_str:
        return render(request, 'error.html', {"message": "Missing UUID."})

    try:
        user_acl = get_object_or_404(UserAcl, uuid=uuid_str)
        user = user_acl.user
    except Exception as e:
        return render(request, 'error.html', {"message": f"Invalid UUID. {e}"})

    form = CustomPasswordResetForm()  # no initial needed since we're not binding username anymore

    return render(request, 'accounts/mgacct.html', {
        'uuid': uuid_str,
        'form': form,
        'username': user.username
    })



def view_login(request):
    if not User.objects.filter().all():
        return redirect('/accounts/create_first_user/')

    if get_api_key('routerfleet'):
        messages.warning(request, 'Login disabled|Login form is disabled. Check integration settings.')
        return redirect('/accounts/logout/')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('/')
            else:
                messages.error(request, _('Invalid username or password.'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def view_logout(request):
    auth.logout(request)
    return render(request, 'accounts/logout.html')

class PasswordResetForm(forms.Form):
    username = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password1")
        pw2 = cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

@login_required
def reset_user_password(request):
    uuid_str = request.GET.get("uuid")
    
    if not uuid_str:
        return render(request, "error.html", {"message": "Missing UUID."})

    try:
        user_acl = get_object_or_404(UserAcl, uuid=uuid_str)
        user = user_acl.user
    except Exception as e:
        return render(request, "error.html", {"message": f"Invalid UUID. {e}"})

    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["password1"]
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password successfully updated.")
            return redirect("login")
        else:
            # This is the key part: display a general error message if form isn't valid
            if "password1" in form.errors or "password2" in form.errors:
                messages.error(request, "Passwords do not match or are invalid.")

            # Rerender the same template with form errors
            return render(
                request,
                "accounts/mgacct.html",
                {"form": form, "uuid": uuid_str, "username": user.username}
            )

    else:
        form = PasswordResetForm()

    return render(
        request,
        "accounts/mgacct.html",
        {"form": form, "uuid": uuid_str, "username": user.username}
    )