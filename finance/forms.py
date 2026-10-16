from decimal import Decimal

from django import forms

from accounts.forms import StyledForm, StyledModelForm
from farms.models import Crop

from .models import FarmExpense, FarmSale


class ExpenseForm(StyledModelForm):
    class Meta:
        model = FarmExpense
        fields = ['title', 'category', 'amount', 'date', 'crop', 'paid_to', 'payment_method',
                  'payment_status', 'description']
        labels = {
            'title': 'Kharcha kis cheez ka', 'category': 'Shreni', 'amount': 'Rashi (Rs)', 'date': 'Tarikh',
            'crop': 'Kis fasal ke liye (optional)', 'paid_to': 'Kisko diya (dukaan / vyakti)',
            'payment_method': 'Payment ka tarika', 'payment_status': 'Payment sthiti', 'description': 'Note',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. 10 bori DAP, Diesel, Bijli bill'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['crop'].queryset = Crop.objects.filter(land__farmer=farmer)
        self.fields['crop'].empty_label = '-- Aam kharcha (kisi fasal ka nahi) --'

    def clean_amount(self):
        a = self.cleaned_data['amount']
        if a <= 0:
            raise forms.ValidationError('Rashi 0 se zyada honi chahiye.')
        return a


class SaleForm(StyledModelForm):
    class Meta:
        model = FarmSale
        fields = ['crop', 'buyer_name', 'sale_place', 'quantity_quintals', 'price_per_quintal',
                  'deductions', 'amount_received', 'sale_date', 'remarks']
        labels = {
            'crop': 'Fasal', 'buyer_name': 'Kharidar / Vyapari ka naam', 'sale_place': 'Kahan becha',
            'quantity_quintals': 'Matra (Quintal)', 'price_per_quintal': 'Bhav (Rs / Quintal)',
            'deductions': 'Katauti (tulai, hamali, commission) Rs', 'amount_received': 'Abhi tak mila hua paisa (Rs)',
            'sale_date': 'Bikri ki tarikh', 'remarks': 'Note',
        }
        widgets = {
            'quantity_quintals': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'price_per_quintal': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Sirf wahi fasal jinka utpadan darj hai
        qs = Crop.objects.filter(land__farmer=farmer, actual_yield_quintal__gt=0)
        if self.instance.pk and self.instance.crop_id:
            qs = (qs | Crop.objects.filter(pk=self.instance.crop_id)).distinct()
        self.fields['crop'].queryset = qs
        self.fields['crop'].empty_label = '-- Fasal chunein --'
        self.fields['crop'].required = True
        self.fields['deductions'].required = False
        self.fields['amount_received'].required = False

    def clean_deductions(self):
        return self.cleaned_data.get('deductions') or Decimal('0')

    def clean_amount_received(self):
        return self.cleaned_data.get('amount_received') or Decimal('0')

    def clean(self):
        data = super().clean()
        crop, qty, rate = data.get('crop'), data.get('quantity_quintals'), data.get('price_per_quintal')
        if crop and qty:
            stock = crop.remaining_stock()
            if self.instance.pk and self.instance.crop_id == crop.pk:
                stock += self.instance.quantity_quintals
            if qty > stock:
                self.add_error('quantity_quintals', f"Stock me sirf {stock} Quintal bacha hai, {qty} Quintal nahi bech sakte.")
        if qty and rate:
            net = qty * rate - data.get('deductions', 0)
            if net < 0:
                self.add_error('deductions', 'Katauti bikri rashi se zyada nahi ho sakti.')
            elif data.get('amount_received', 0) > net:
                self.add_error('amount_received', f"Mila hua paisa net rashi (Rs {net}) se zyada nahi ho sakta.")
        return data


class PaymentForm(StyledForm):
    amount = forms.DecimalField(label='Rashi (Rs)', min_value=0.01, decimal_places=2, max_digits=12)
