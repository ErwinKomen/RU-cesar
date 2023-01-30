"""
Definition of forms for the BASIC app.
"""

from django import forms
from django.forms import ModelForm


# =============== My own form class ==========================

class BasicForm(ModelForm):

    def is_valid(self):
        # Do default is valid
        valid = super(BasicForm, self).is_valid()

        # If it's False, return
        if valid: 

            # Otherwise: try myself.
            cd = self.cleaned_data

            if not cd is None:
                for k,v in cd.items():
                    if isinstance(v,str) and "<script" in v:
                        # provide an appropriate warning message
                        valid = False
                        self.errors[k] = "Don't include JS in a text field"
                        # break
        # Return what we have
        return valid

