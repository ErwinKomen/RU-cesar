from django.forms.widgets import Textarea
from django.utils.safestring import mark_safe
import os

class OriginalSeekerTextarea(Textarea):
    def render(self, name, value, attrs = None, renderer = None):
      output = []
      # Check for none-type
      if value != None:
          # Create a span containing the text
          sTextValue = value.strip()
          if len(sTextValue) > 60:
              sTextValue = sTextValue[:60] + "..."
          sTextValue = sTextValue.replace("\n", "<br>")
          output.append("<span class=\"td-toggle-textarea {}\">{}</span>".format(
            "hidden" if sTextValue == "" else "",
            sTextValue))
          # Start a span around the textarea
          output.append("<span class=\"td-textarea {}\">".format(
            "" if sTextValue == "" else "hidden"
            ))
      output.append(super(SeekerTextarea, self).render(name, value, attrs))
      if value != None:
          output.append("</span>")
      # Combine and return
      return mark_safe('\n'.join(output))

class SeekerTextarea(Textarea):
    pass