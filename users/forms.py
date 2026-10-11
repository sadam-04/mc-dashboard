from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from django import forms
from django.core.cache import cache
from .models import PissUser

import logging

logger = logging.getLogger(__name__)


# from users.models import MyUser

class MyLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(MyLoginForm, self).__init__(*args, **kwargs)

    username = UsernameField(widget=forms.TextInput(
        attrs={
            'class': 'text-input',
            'placeholder': 'username',
            'id': 'username-field'
        }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'text-input',
            'placeholder': 'password',
            'id': 'password-field',
        }
))

class MySignupForm(UserCreationForm):
    pin = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'class': 'text-input', 'placeholder': 'PIN'}))
    # mc_username = forms.CharField(widget=forms.HiddenInput())
    # mc_uuid = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({'class': 'text-input'})
        self.fields['username'].widget.attrs.update({'placeholder': 'MC Username'})
                        
        self.fields['password1'].widget.attrs.update({'class': 'text-input'})
        self.fields['password2'].widget.attrs.update({'class': 'text-input'})

    class Meta(UserCreationForm.Meta):
        model = PissUser
        fields = ("username",)

    def clean(self):
        cleaned_data = super().clean()
        my_username = cleaned_data.get("username")
        pin = cleaned_data.get("pin")
        
        if my_username and pin:
            cache_key = f"mc_registration_{my_username}"
            stored_pin = cache.get(cache_key)

            if not stored_pin:
                self.add_error('pin', "wrong pin cuh 1")
            elif stored_pin != pin:
                self.add_error('pin', "wrong pin cuh 2")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        
        if commit:
            stored_uuid = cache.get(f"mc_uuid_{self.cleaned_data['username']}")
            if not stored_uuid:
                logger.warning("THERE is no cached uuid for this user somehow. this shouldn't be possible")
            else:
                user.minecraft_uuid = stored_uuid
        
            user.save()

            # PlayerProfile.objects.create(user=user, mc_username=self.cleaned_data['mc_username'], mc_uuid=self.cleaned_data['mc_uuid'])
            # Invalidate the PIN so it can't be reused
            cache.delete(f"mc_registration_{self.cleaned_data['username']}")
        return user