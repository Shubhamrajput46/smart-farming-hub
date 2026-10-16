from accounts.forms import StyledModelForm
from farms.models import Crop

from .models import Reminder


class ReminderForm(StyledModelForm):
    class Meta:
        model = Reminder
        fields = ['title', 'due_date', 'crop', 'notes']
        labels = {'title': 'Kya karna hai', 'due_date': 'Kab tak', 'crop': 'Fasal (optional)', 'notes': 'Note'}

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['placeholder'] = 'e.g. Gehun me pehla paani, Thresher book karna'
        self.fields['crop'].queryset = Crop.objects.filter(land__farmer=farmer)
        self.fields['crop'].empty_label = '-- Kisi fasal se nahi jura --'
