"""
Definition of forms for the LINGO app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea

# Application specific
from cesar.lingo.models import *

class ExperimentForm(ModelForm):
    meta_fields = ['ptcpid', 'age', 'gender', 'engfirst', 'lngfirst', 'lngother', 'eduother', 'edu', 'teaches', 'email']
    meta_initial = [
        "Wat is uw participant ID?",
        "Wat is uw leeftijd?",
        "Wat is uw geslacht?",
        "Is Engels uw moedertaal?",
        "Wat is uw eerste taal?",
        "Welke andere talen kent u?",
        "Anders: ",
        "Wat is uw hoogste school?",
        "Welk vak doceert u?",
        "Wat is uw email adres (optioneel)?"
        ]

    class Meta:
        model = Experiment
        fields = ['title', 'home', 'msg', 'responsecount', 'consent', 'ptcpfields', 'status' ]
        widgets={'title':   forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Title as will appear in the list of experiments'}),
                 'home':    forms.TextInput(attrs={'style': 'width: 20%;', 'placeholder': 'Experiment code (default is [tcpf])'}),
                 'msg':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;', 
                                                    'placeholder': 'Purpose of this experiment (for your own administration)'}),
                 'responsecount': forms.NumberInput(attrs={'style': 'width: 100%;', 'placeholder': 'Number of responses per participant'}),
                 'ptcpfields':  forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;'}),
                 'consent':     forms.Textarea(attrs={'rows': 2, 'cols': 40, 'style': 'height: 80px; width: 100%;', 
                                                    'placeholder': 'Consent statement that any participant will need to agree with. This can also contain an explanation of the experiment.'}),
                 'status':      forms.Select()
                 }

    def __init__(self, *args, **kwargs):
        super(ExperimentForm, self).__init__(*args, **kwargs)
        self.fields['home'].required = False
        self.fields['msg'].required = False
        self.fields['title'].required = False
        
        self.fields['status'].required = False
        self.fields['status'].choices = build_abbr_list(EXPERIMENT_STATUS)

        # Get the instance
        instance = None
        oMeta = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
            oMeta = json.loads(instance.metafields)
            
        for idx, fname in enumerate(self.meta_fields):
            fld_include = "meta_{}_include".format(fname)
            fld_text = "meta_{}_text".format(fname)
            self.fields[fld_include] = forms.ChoiceField(required=False, widget= forms.Select(attrs={'style': 'width: 100%;'}))
            self.fields[fld_text] = forms.CharField(label=fname, max_length=255, required=False, 
                                                    widget = forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Text for field: [{}]'.format(fname)}))
            self.fields[fld_include].choices = build_abbr_list(EXPERIMENT_YESNO, language="nld", maybe_empty=True)
            # Set initial values
            if instance and fname in oMeta:
                oMetaField = oMeta[fname]
                # Take initial values from instance
                self.fields[fld_include].initial = "y" if oMetaField['include'] else "n"
                self.fields[fld_text].initial = oMetaField['text']
            else:
                self.fields[fld_include].initial = "y"
                self.fields[fld_text].initial = self.meta_initial[idx]

        # self.fields['meta_ptcpid_include'].choices = build_abbr_list(EXPERIMENT_YESNO, language="nld", maybe_empty=True)



class ParticipantForm(ModelForm):

    class Meta:
        model = Participant
        fields = ['ptcpid', 'age', 'gender', 'engfirst', 'lngfirst', 'lngother', 'edu', 'eduother', 'teaches', 'email']
        widgets={'ptcpid':      forms.TextInput(attrs={'style': 'width: 40%;', 'placeholder':'Jouw participant ID'}),
                 'age':         forms.TextInput(attrs={'style': 'width: 40%;', 'placeholder':'Leeftijd (getal)'}),
                 'gender':      forms.Select(),
                 'engfirst':    forms.Select(),
                 'lngfirst':    forms.TextInput(attrs={'style': 'width: 50%;', 'placeholder':'Uw eerste taal'}),
                 'lngother':    forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Noem de andere talen die u kent'}),
                 'eduother':    forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Beschrijf het schooltype waar u lesgeeft'}),
                 'edu':         forms.Select(),
                 'teaches':     forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Het vak dat u doceert'}),
                 'email':       forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Uw e-mailadres'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ParticipantForm, self).__init__(*args, **kwargs)
        # This is DUTCH, so we need to load other choices
        self.fields['gender'].choices = build_abbr_list(EXPERIMENT_GENDER, language="nld", maybe_empty=True, sortcol=0)
        self.fields['engfirst'].choices = build_abbr_list(EXPERIMENT_YESNO, language="nld", maybe_empty=True)
        self.fields['edu'].choices = build_abbr_list(EXPERIMENT_EDU, language="nld", maybe_empty=True, sortcol=0)


class AnswerForm(forms.Form):
    # The ID of the Participant (assigned by the Django system)
    ptcp_id = forms.CharField(label="Participant id", max_length=100)
    # A number of different answers
    answer1 = forms.CharField(label="Answer1", max_length=255, required=False)
    answer2 = forms.CharField(label="Answer2", max_length=255, required=False)
    answer3 = forms.CharField(label="Answer3", max_length=255, required=False)
    answer4 = forms.CharField(label="Answer4", max_length=255, required=False)
    answer5 = forms.CharField(label="Answer5", max_length=255, required=False)
    answer6 = forms.CharField(label="Answer6", max_length=255, required=False)
    answer7 = forms.CharField(label="Answer7", max_length=255, required=False)
    answer8 = forms.CharField(label="Answer8", max_length=255, required=False)
    answer9 = forms.CharField(label="Answer9", max_length=255, required=False)
    motivation = forms.CharField(label="Motivation", required=False,
        widget= forms.TextInput(attrs={'placeholder': 'Toelichting...', 'style': 'width: 100%; background-color: whitesmoke;'}))


class QdataListForm(forms.ModelForm):
    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = Qdata
        fields = ['qmeta', 'qtopic', 'qtext', 'include']
        widgets={'qmeta':   forms.TextInput(attrs={'placeholder': 'Metadata...', 'style': 'width: 100%;'}),
                 'qtopic':  forms.TextInput(attrs={'placeholder': 'Topic...', 'style': 'width: 100%;'}),
                 'qtext':   forms.TextInput(attrs={'placeholder': 'The question itself...', 'style': 'width: 100%;'}),
                 'include': forms.TextInput(attrs={'placeholder': 'Is this text included?...', 'style': 'width: 100%;'})
                 }
