from django.db import models

# Attempt to input FROG
try:
    from frog import Frog, FrogOptions
    froglocation = "local"
    # See: https://frognlp.readthedocs.io/en/latest/pythonfrog.html
except:
    # It is not there...
    froglocation = "remote"
    frogurl = "https://webservices-lst.science.ru.nl/frog"
    from clam.common.client import *



class FrogLink(models.Model):
    """This provides the basic link with FROG

    Can be either frog local or frog remote, through the CLAM service
    """

    pass
    