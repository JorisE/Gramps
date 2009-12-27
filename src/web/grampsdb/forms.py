# forms.py forms for Django web project 

from django import forms
from web.grampsdb.models import *
from django.forms.models import inlineformset_factory
from django.forms.models import BaseModelFormSet
from django.forms.widgets import TextInput
import datetime

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person

    '''def clean(self):
        cleaned_data['last_changed'] = datetime.datetime.now()
        super(PersonForm, self).clean() # validate based on model
        return self.cleaned_data'''
        
class NameForm(forms.ModelForm):
    class Meta:
        model = Name
        # Exclude these, so they don't get checked:
        exclude = ["order", "calendar", "modifier", 
                   "quality",
                   #"quality_estimated", "quality_calculated", 
                   #"quality_interpreted", 
                   "year1", "day1", "month1",
                   "sortval", "newyear", "person"]
    # Add these because they are TextFields, which render as
    # Textareas:
    surname = forms.CharField(required=False, 
                              widget=TextInput(attrs={'size':'30'}))
    first_name = forms.CharField(label="Given", 
                                 required=False, 
                                 widget=TextInput(attrs={'size':'30'}))
    title = forms.CharField(required=False, 
                            widget=TextInput(attrs={'size':'30'}))
    prefix = forms.CharField(required=False, 
                             widget=TextInput(attrs={'size':'30'}))
    suffix = forms.CharField(required=False, 
                             widget=TextInput(attrs={'size':'30'}))
    call = forms.CharField(label="Callname", 
                           required=False, 
                           widget=TextInput(attrs={'size':'30'}))
    patronymic = forms.CharField(required=False, 
                                 widget=TextInput(attrs={'size':'30'}))
    group_as = forms.CharField(required=False, 
                               widget=TextInput(attrs={'size':'30'}))
    text = forms.CharField(label="Date",
                           required=False, 
                           widget=TextInput(attrs={'size':'30'}))

'''class NameFormset(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.form = NameForm
        super(NameFormset, self).__init__(*args, **kwargs)
        
def makeNameFormset(pid):
    class NameFormset(BaseFormSet):
        def __init__(self, *args, **kwargs):
            self.form = NameForm
            self.queryset = Name.objects.filter(person=pid)
            super(NameFormset, self).__init__(*args, **kwargs)
        def clean(self):
            super(NameFormset, self).clean() # validate based on model
            if any(self.errors):
            # formset is not valid as long as any one form is invalid
                return
            # allow only one name per person to be preferred
            ctPref = 0
            for i in range(0, self.total_form_count()):
                form = self.forms[i]
                ctPref += form.cleaned_data['preferred']
            if ctPref > 1:
                raise forms.ValidationError, "Only one name may be the preferred name."
    return NameFormset'''

NameInlineFormSet = inlineformset_factory(Person, Name,
                                          fields=('preferred','prefix','first_name',
                                                  'surname','suffix','name_type'),
                                          form=NameForm)

def cleanPreferred(fmst):
    if fmst.total_form_count() == 3: # person has no names (assumes default 3 extra forms)
        return "Error: Each person must have at least one name."
    ctPref = 0
    for i in range (0,fmst.total_form_count()-3):
        form = fmst.forms[i]
        try: # when preferred is false, its value is not in the form data
            if form.data[fmst.prefix + '-' + str(i) + '-preferred'] == 'on':
                val = 1
            else:
                val = 0
        except:
            val = 0
        ctPref += val
    if ctPref != 1:
        return "Error: Exactly one name may be the preferred name."
    else:
        return "none"
