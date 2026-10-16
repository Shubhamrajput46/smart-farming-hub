from django import forms

from accounts.forms import StyledForm, StyledModelForm

from .models import Crop, CropOperationLog, Land


class LandForm(StyledModelForm):
    class Meta:
        model = Land
        fields = ['title', 'khasra_number', 'total_area_acres', 'soil_type', 'water_source',
                  'irrigation_type', 'ownership', 'notes']
        labels = {
            'title': 'Khet ka naam', 'khasra_number': 'Khasra Number', 'total_area_acres': 'Kul Rakba (Acre)',
            'soil_type': 'Mitti', 'water_source': 'Paani ka source', 'irrigation_type': 'Sinchai ka tarika',
            'ownership': 'Malikana', 'notes': 'Note',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Nadi wala khet'}),
            'total_area_acres': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def clean_total_area_acres(self):
        area = self.cleaned_data['total_area_acres']
        if area <= 0:
            raise forms.ValidationError('Rakba 0 se zyada hona chahiye.')
        if self.instance.pk:
            sown = self.instance.sown_acres()
            if area < sown:
                raise forms.ValidationError(f'Is khet me {sown} Acre me fasal boyi hai, rakba usse kam nahi ho sakta.')
        return area


class CropForm(StyledModelForm):
    class Meta:
        model = Crop
        fields = ['land', 'name', 'season', 'season_year', 'allocated_acres', 'seed_info', 'sowing_date',
                  'expected_harvest_date', 'stage', 'expected_yield_quintal', 'notes']
        labels = {
            'land': 'Khet', 'name': 'Fasal / Kism', 'season': 'Mausam', 'season_year': 'Saal',
            'allocated_acres': 'Kitne Acre me boyi', 'seed_info': 'Beej (kism / matra)',
            'sowing_date': 'Buwai ki tarikh', 'expected_harvest_date': 'Katayi ki anumaanit tarikh',
            'stage': 'Abhi ki sthiti', 'expected_yield_quintal': 'Anumaanit utpadan (Quintal)', 'notes': 'Note',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Gehun Sharbati, Soybean 9560'}),
            'allocated_acres': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'expected_yield_quintal': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['land'].queryset = Land.objects.filter(farmer=farmer)
        self.fields['land'].empty_label = '-- Khet chunein --'
        # "Completed" yahan se nahi, Harvest record karke hi hota hai
        self.fields['stage'].choices = [c for c in Crop.STAGE_CHOICES if c[0] != 'Completed']
        if self.instance.pk and self.instance.stage == 'Completed':
            self.fields['stage'].choices = Crop.STAGE_CHOICES

    def clean(self):
        data = super().clean()
        land, acres = data.get('land'), data.get('allocated_acres')
        sow, harvest = data.get('sowing_date'), data.get('expected_harvest_date')
        if sow and harvest and harvest <= sow:
            self.add_error('expected_harvest_date', 'Katayi ki tarikh buwai ke baad honi chahiye.')
        if land and acres is not None:
            if acres <= 0:
                self.add_error('allocated_acres', 'Acre 0 se zyada hone chahiye.')
            elif data.get('stage') != 'Completed':
                free = land.available_area(exclude_crop_id=self.instance.pk)
                if acres > free:
                    self.add_error('allocated_acres',
                                   f"'{land.title}' me sirf {free} Acre jagah bachi hai (kul {land.total_area_acres}).")
        return data


class HarvestForm(StyledForm):
    actual_yield_quintal = forms.DecimalField(label='Kul utpadan (Quintal)', min_value=0.01, decimal_places=2, max_digits=9)
    actual_harvest_date = forms.DateField(label='Katayi ki tarikh')
    mark_completed = forms.BooleanField(label='Fasal poori ho gayi (khet khaali karein)', required=False, initial=True)


class CropOperationForm(StyledModelForm):
    total_cost = forms.DecimalField(label='Kul Kharcha (Rs)', required=False, min_value=0, decimal_places=2, max_digits=10,
                                    help_text='Khaali chhodein to majdoor x dihadi se apne-aap judega.')

    class Meta:
        model = CropOperationLog
        fields = ['crop', 'operation_type', 'date', 'labour_count', 'labour_cost_per_person',
                  'material_used', 'hours_run', 'total_cost', 'notes']
        labels = {
            'crop': 'Fasal', 'operation_type': 'Kaam', 'date': 'Tarikh', 'labour_count': 'Majdoor (sankhya)',
            'labour_cost_per_person': 'Dihadi per majdoor (Rs)', 'material_used': 'Saamaan (khad / dawai)',
            'hours_run': 'Tractor / Motor ke ghante', 'notes': 'Note',
        }
        widgets = {
            'material_used': forms.TextInput(attrs={'placeholder': 'e.g. 2 bori Urea, 250ml Tilt'}),
            'hours_run': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Crop.objects.filter(land__farmer=farmer, is_active=True)
        if self.instance.pk:
            qs = Crop.objects.filter(land__farmer=farmer, pk__in=[self.instance.crop_id]) | qs
        self.fields['crop'].queryset = qs.distinct()
        self.fields['crop'].empty_label = '-- Fasal chunein --'

    def clean_total_cost(self):
        return self.cleaned_data.get('total_cost') or 0
