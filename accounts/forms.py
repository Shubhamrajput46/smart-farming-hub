from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import FarmerDocument, FarmerProfile


class StyledFormMixin:
    """Har field par CSS class + date picker lagata hai (widgets baar-baar nahi likhne padte)."""

    def style_fields(self):
        for field in self.fields.values():
            if isinstance(field, forms.DateField) and not isinstance(field, forms.DateTimeField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check'
            else:
                widget.attrs['class'] = (widget.attrs.get('class', '') + ' form-input').strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('rows', 3)


class StyledForm(StyledFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class StyledModelForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class StyledAuthForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields['username'].widget.attrs.update({'placeholder': 'Username', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'placeholder': 'Password'})


class SignupForm(StyledFormMixin, UserCreationForm):
    full_name = forms.CharField(label='Poora Naam', max_length=150)
    phone = forms.CharField(label='Mobile Number', max_length=20)
    village = forms.CharField(label='Gaon', max_length=100)
    district = forms.CharField(label='Zila', max_length=100, initial='Indore')
    state = forms.CharField(label='Rajya', max_length=100, initial='Madhya Pradesh')

    class Meta:
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Password dobara'
        self.order_fields(['full_name', 'phone', 'village', 'district', 'state',
                           'username', 'password1', 'password2'])
        self.style_fields()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            FarmerProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                phone=self.cleaned_data['phone'],
                village=self.cleaned_data['village'],
                district=self.cleaned_data['district'],
                state=self.cleaned_data['state'],
            )
        return user


class ProfileForm(StyledModelForm):
    class Meta:
        model = FarmerProfile
        fields = ['full_name', 'avatar', 'phone', 'village', 'district', 'state', 'experience_years']
        labels = {
            'full_name': 'Poora Naam', 'avatar': 'Photo', 'phone': 'Mobile',
            'village': 'Gaon', 'district': 'Zila', 'state': 'Rajya',
            'experience_years': 'Kheti ka anubhav (saal)',
        }


class DocumentForm(StyledModelForm):
    class Meta:
        model = FarmerDocument
        fields = ['title', 'doc_type', 'file', 'expiry_date']
        labels = {'title': 'Document ka naam', 'doc_type': 'Prakaar',
                  'file': 'File (photo / PDF)', 'expiry_date': 'Khatam hone ki tarikh (agar ho)'}
