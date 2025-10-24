# order/forms.py
from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['quantity']   # cuma quantity yang boleh diisi user
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }
