from django import forms
from .models import Nomenclature, LSI

class NomenclatureForm(forms.ModelForm):
    class Meta:
        model = Nomenclature
        fields = '__all__'
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'uuid': forms.TextInput(attrs={'placeholder': 'Например: e9b1fd3b-bfd5-4931-a5f2-b27fa98899a7'}),
            'abbreviation': forms.TextInput(attrs={'placeholder': 'Например: ИЛ-76'}),
            'spk_nomenclature_type': forms.TextInput(attrs={'placeholder': 'Например: ВС'}),
            'internal_code': forms.TextInput(attrs={'placeholder': 'Например: 001234'}),
            'cipher': forms.TextInput(attrs={'placeholder': 'Например: 70.03'}),
            'checksum': forms.TextInput(),
            'short_name': forms.TextInput(attrs={'placeholder': 'Например: Илюшин-76'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Например: Транспортный самолет Ил-76МД'}),
            'deletion_mark': forms.CheckboxInput(),
            'archived': forms.CheckboxInput(),
        }

class LSIForm(forms.ModelForm):
    class Meta:
        model = LSI
        fields = '__all__'
        widgets = {
            'uuid': forms.TextInput(attrs={'placeholder': 'Например: e9b1fd3b-bfd5-4931-a5f2-b27fa98899a7'}),
            'cipher': forms.TextInput(attrs={'placeholder': 'Например: 70.03'}),
            'position_name': forms.TextInput(attrs={'placeholder': 'Например: Самолет'}),
            'object_type_code': forms.TextInput(attrs={'placeholder': 'Например: 8c1b6da5-ec4c-47c9-9c85-16da69876baa'}),
            'group_indicator': forms.CheckboxInput(),
            'deletion_mark': forms.CheckboxInput(),
            'drawing_number': forms.TextInput(attrs={'placeholder': '0'}),
            'quantity': forms.NumberInput(attrs={'min': '0'}),
        } 