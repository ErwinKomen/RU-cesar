"""
Definition of forms for the BRIEF app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

# Application specific
from cesar.brief.models import *

YES_NO_CHOICE = [('','(make a choice)'), ('yes', 'Yes'), ('no', 'No')]

class ProjectForm(ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'ptype', 'user']
        widgets={'name':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Name of this project...'}),
                 'description': forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Description of the project...'}),
                 'status':      forms.Select(attrs={'style': 'width: 100%;'}),
                 'ptype':       forms.Select(attrs={'style': 'width: 100%;'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.fields['user'].required = False
        self.fields['name'].required = False
        self.fields['description'].required = False
        self.fields['ptype'].required = False
        self.fields['status'].required = False
        self.fields['status'].choices = build_abbr_list(PROJECT_STATUS)
        self.fields['ptype'].choices = build_abbr_list(PROJECT_PROGRESS)


class QuestionsForm(ModelForm):

    class Meta:
        model = Project
        fields = []

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(QuestionsForm, self).__init__(*args, **kwargs)

        # Now add one field for every BriefQuestion
        for question in BriefQuestion.objects.all():
            # Construct the field name
            field_name = "bq-{}".format(question.id)

            # Get the answer to this question (if existing)
            answer = ""
            if 'instance' in kwargs:
                instance = kwargs['instance']
                aq = AnswerQuestion.objects.filter(project=instance, question=question).first()
                if aq != None:
                    answer = aq.content

            # Make sure the placeholder is alright
            placeholder = ""
            if question.placeholder != None:
                placeholder = "{}...".format(question.placeholder.strip())

            # Construct a field, depending on the field type
            if question.rtype == "line":
                self.fields[field_name] = forms.CharField(
                    required=False, 
                    widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': placeholder}))
            elif question.rtype == "mline":
                self.fields[field_name] = forms.CharField(
                    required=False, 
                    widget=forms.Textarea(attrs={'rows': 1, 'cols': 40, 
                                                 'style': 'min-height: 30px; width: 100%; overflow-y: auto;', 
                                                 'placeholder': placeholder}))
            elif question.rtype == "boole":
                self.fields[field_name] = forms.ChoiceField(
                    required=False, choices=YES_NO_CHOICE, 
                    widget=forms.Select(attrs={'style': 'width: 50%;'}))
            if answer != "":
                self.fields[field_name].initial = answer
            
            
class AnswerEntryForm(ModelForm):
    """The answer to one entry"""

    class Meta:
        model = AnswerEntry
        fields = ['content', 'entry', 'question', 'project']
        widgets={'content':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Answer...'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(AnswerEntryForm, self).__init__(*args, **kwargs)

        self.fields['question'].required = False
        self.fields['entry'].required = False
        self.fields['content'].required = False
        if 'instance' in kwargs:
            instance = kwargs['instance']


class ProductForm(ModelForm):
    """One Scripture product"""
    new_name = forms.CharField(label=_("Name"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'The name of this product...'}))
    new_scripture = forms.CharField(label=_("Scripture"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'The books or passages included in this product...'}),
                help_text="list books, passages")
    new_format = forms.CharField(label=_("Format"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'The format of this product...'}), help_text="text / audio / video")
    new_media = forms.CharField(label=_("Media"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'The media on which this product is available...'}),
                help_text="print / digital / broadcast / live performance etc.")
    new_goal = forms.CharField(label=_("Goal"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'Desires, needs, concerns...'}),
                help_text="What desire(s), felt need(s), concern(s) and/or value(s) does this product address?")
    new_audience = forms.CharField(label=_("Audience"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'Audience(s) this product is aimed for...'}))
    new_timing = forms.CharField(label=_("Timing"), required=False, widget=forms.TextInput(attrs={'style': 'width: 100%;', 
                'placeholder':'Timing...'}))

    class Meta:
        model = BriefProduct
        fields = ['project', 'name', 'scripture', 'format', 'media', 'goal', 'audience', 'timing']
        widgets={'name':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'The name of this product...'}),
                 'scripture':   forms.TextInput(attrs={'style': 'width: 100%;', 
                                                       'placeholder':'The books or passages included in this product...'}),
                 'format':      forms.TextInput(attrs={'style': 'width: 100%;', 
                                'placeholder':'The format of this product...'}), 
                 'media':       forms.TextInput(attrs={'style': 'width: 100%;', 
                                'placeholder':'The media on which this product is available...'}),
                 'goal':        forms.TextInput(attrs={'style': 'width: 100%;', 
                                'placeholder':'Desires, needs, concerns...'}),
                 'audience':    forms.TextInput(attrs={'style': 'width: 100%;', 
                                'placeholder':'Audience(s) this product is aimed for...'}),
                 'timing':      forms.TextInput(attrs={'style': 'width: 100%;', 
                                'placeholder':'Timing...'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ProductForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = False
        self.fields['scripture'].required = False
        self.fields['format'].required = False
        self.fields['media'].required = False
        self.fields['goal'].required = False
        self.fields['audience'].required = False
        self.fields['timing'].required = False
        if 'instance' in kwargs:
            instance = kwargs['instance']

