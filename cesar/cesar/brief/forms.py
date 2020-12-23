"""
Definition of forms for the BRIEF app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory, BaseFormSet
from django.forms.widgets import Textarea

# Application specific
from cesar.brief.models import *

YES_NO_CHOICE = [('','(make a choice)'), ('yes', 'Yes'), ('no', 'No')]

class ProjectForm(ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'ptype']
        widgets={'name':        forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Name of this project...'}),
                 'description': forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder':'Description of the project...'}),
                 'status':      forms.Select(attrs={'style': 'width: 100%;'}),
                 'ptype':       forms.Select(attrs={'style': 'width: 100%;'})
                 }

    def __init__(self, *args, **kwargs):
        # First perform the default thing
        super(ProjectForm, self).__init__(*args, **kwargs)

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
            
            



