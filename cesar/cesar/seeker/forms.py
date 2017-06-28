"""
Definition of forms for the SEEKER app.
"""

from django import forms
from django.forms import ModelForm, formset_factory, modelformset_factory
from cesar.seeker.models import *

WORD_ORIENTED = 'w'
CONSTITUENT_ORIENTED = 'c'
TARGET_TYPE_CHOICES = (
    (WORD_ORIENTED, 'Word(s)'),
    (CONSTITUENT_ORIENTED, 'Constituent(s)'),
)

SEARCHMAIN_WRD_FUNCTIONS = (
        ('w-m', 'Word matches'),
        ('wn-m', 'Next word matches'),
    )
SEARCHMAIN_CNS_FUNCTIONS = (
        ('c-m', 'Category matches'),
        ('c--m', 'Child category matches'),
    )


class VariableForm(ModelForm):
    class Meta:
        model = Variable
        fields = ['name', 'description']


class GatewayForm(ModelForm):
    class Meta:
        model = Gateway
        fields = ['name', 'description']

    def is_valid(self):
        # Do default is valid
        valid = super(GatewayForm, self).is_valid()

        # If it's False, return
        if not valid: return valid

        # Otherwise: try myself.
        cd = self.cleaned_data
        obj = self.instance
        if obj == None or obj.name == "":
            return False
        else:
            return True


class ConstructionWrdForm(ModelForm):
    # function_sc = forms.ChoiceField(choices=SEARCHMAIN_WRD_FUNCTIONS, required = True)
    value = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}))
    class Meta:
        model = Construction
        fields = ['name']

    #def save(self, *args, **kwargs):
    #    # Create a search for this one
    #    value=self.value
    #    search = SearchMain.create_item('word-group', value, 'groupmatches')

    #    # Get the gateway we are under
    #    gateway = None

    #    # Make sure the construction gets the correct search and gateway
    #    self.instance.search = search
    #    self.instance.gateway = gateway

    #    # Now save the construciotn
    #    constructionwrd = super(ConstructionWrdForm, self).save( *args, **kwargs)

    #    # Return what we have
    #    return constructionwrd


class ConstructionCnsForm(ModelForm):
    function_sc = forms.ChoiceField(choices=SEARCHMAIN_CNS_FUNCTIONS, required = True)
    value = forms.CharField(required=True)
    class Meta:
        model = Construction
        fields = ['name', 'search']
        widgets={
          'value': forms.Textarea(attrs={'rows': 2, 'cols': 40})
          }


class SeekerResearchForm(ModelForm):
    # A research form should also have the Word/Constituent choice
    targetType = forms.ChoiceField(choices=TARGET_TYPE_CHOICES, required=True)

    # Make sure we take over the actual Research elements,
    #   but exclude the one-to-one 'gateway' link
    class Meta:
        model = Research
        fields = ['name', 'purpose']
        widgets={
          'purpose': forms.Textarea(attrs={'rows': 1, 'cols': 100})
          }

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(SeekerResearchForm, self).__init__(*args, **kwargs)

        # get the post-data
        data = args[0] if args else kwargs.get('data', None)

        # Do we have data?
        if data:
            # There is POST data, so fill the forms with the required information
            self.gateway_data = {key: data[key] for key in data if key.startswith('gateway-')}
            if hasattr(self.instance, 'gateway'):
                self.gateway_form = GatewayForm(
                    instance = self.instance.gateway,
                    prefix='gateway',
                    data=self.gateway_data
                )
            else:
                self.gateway_form = GatewayForm(
                    prefix='gateway',
                    data=self.gateway_data
                )
        else:
            # Didn't get any POST data
            # Fill the form with the gateway data, or create a blank form
            if hasattr(self.instance, 'gateway') and  self.instance.gateway:
                # There is a gateway, so use it
                self.gateway_form = GatewayForm(
                    instance = self.instance.gateway,
                    prefix='gateway'
                )
            else:
                # Create a new form
                self.gateway_form = GatewayForm(prefix='gateway')

    def is_valid(self):
        if not self.gateway_form.is_valid():
            return False
        return super(SeekerResearchForm, self).is_valid()

    def clean(self):
        if not self.gateway_form.is_valid():
            raise forms.ValidationError("Gateway not valid")

    def save(self, *args, **kwargs):
        # Save the gateway form first
        gateway = self.gateway_form.save()

        # now make sure the SeekerResearchForm has the gateway
        self.instance.gateway = gateway

        # Also make sure that all Constructions get the link to this gateway

        # Now save the larger form
        research = super(SeekerResearchForm, self).save( *args, **kwargs)

        # THIS IS NOT NEEDED ANYMORE:
        ## Get the correct gateway
        #research.gateway = gateway

        # Now save the research object
        research.save()

        # And return it
        return research

    def has_changed(self):
        return super(SeekerResearchForm,self).has_changed() or self.gateway_form.has_changed()


