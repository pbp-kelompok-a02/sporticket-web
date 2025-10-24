from django import forms
from .models import Review
from order.models import Order

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'komentar']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'for-control',
                'min': 1,
                'max': 5,
                'placeholder': '1-5'
            }),
            'komentar': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write review (optional)....'
            })
        }