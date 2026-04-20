from django import forms

from .models import Complaint


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class AgentComplaintForm(forms.Form):
    status = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-select'}))
    notes_append = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Optional note to append',
        }),
    )

    def __init__(self, *args, complaint=None, **kwargs):
        super().__init__(*args, **kwargs)
        if complaint:
            statuses = list(Complaint.Status)
            current = [s.value for s in statuses].index(complaint.status)
            self.fields['status'].choices = [(s.value, s.label) for s in statuses[current:]]
            self.fields['status'].initial = complaint.status
