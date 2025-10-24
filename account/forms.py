from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm
from .models import Profile

User = get_user_model()


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm password')
    phone_number = forms.CharField(max_length=30, required=False)
    profile_photo = forms.ImageField(required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Email already registered.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match.')
        return cleaned

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            if Profile.objects.filter(phone_number=phone_number).exists():
                raise ValidationError('Phone number already registered.')
        return phone_number or None

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
        )
        profile = Profile.objects.create(
            user=user,
            name=data['name'],
            role=data.get('role', 'Buyer'),
            phone_number=data.get('phone_number') or None,
            profile_photo=data.get('profile_photo') if data.get('profile_photo') else None,
        )
        return user
    
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
class ProfileUpdateForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = ['name', 'phone_number', 'profile_photo']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise ValidationError('Name cannot be empty.')
        return name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        profile_id = self.instance.pk
        if phone_number:
            if Profile.objects.filter(phone_number=phone_number).exclude(pk=profile_id).exists():
                raise ValidationError('Phone number already registered by another account.')
        return phone_number or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # inisialisasi field email dari User terkait
        if self.instance and getattr(self.instance, 'user', None):
            self.fields['email'].initial = getattr(self.instance.user, 'email', '')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        # exclude user yang sedang diupdate dari pengecekan keunikan
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.user.pk).exists():
            raise ValidationError('Email already registered by another account.')
        return email

    def save(self, commit=True):
        # simpan field profile terlebih dahulu
        profile = super().save(commit=False)
        # update email dan username user terkait ke email baru
        new_email = self.cleaned_data.get('email')
        user = profile.user
        if new_email and new_email.lower() != (user.email or '').lower():
            user.email = new_email
            # pastikan username juga diupdate agar dapat login dengan email baru
            try:
                user.username = new_email
            except Exception:
                user.username = new_email
            user.save(update_fields=['email', 'username'])

        if commit:
            profile.save()
        return profile