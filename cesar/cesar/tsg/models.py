import json
from django.db import models
from django.utils import timezone
from cesar.utils import ErrHandle

MAXPARAMLEN = 100

class TsgInfo(models.Model):
    """Each instance contains a bit of information that can be used by the TSG"""

    # [1] Each bit of TSG information consists of a key and a value
    infokey = models.CharField("Key to this bit of information", max_length=MAXPARAMLEN)
    # [0-1] We expect a value, but it may be empty upon start
    infoval = models.TextField("The information itself", blank=True, default="")
    # [1] Information history as stringified JSON object
    history = models.TextField("History", default = "[]")
    # [1] Each TsgInfo has been created at one point in time
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.infokey

    def get_value(key):
        """Given a key, provide its value, or NONE if it does not exist"""

        oErr = ErrHandle()
        infoval = None
        try:
            obj = TsgInfo.objects.filter(infokey__iexact=key).first()
            if obj != None:
                infoval = obj.infoval
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgInfo/get_value")
        return infoval


class TsgHandle(models.Model):
    """One handle links to one url"""

    # [1] The handle code
    code = models.CharField("Handle code", max_length=MAXPARAMLEN)
    # [1] The current URL this handle links to
    url = models.URLField("Handle URL")
    # [1] The handle domain
    domain = models.CharField("Handle base url", max_length=MAXPARAMLEN, default="21.11114")
    # [1] Information on this handle in stringified JSON
    info = models.TextField("Information", default = "[]")
    # [1] Each handle code also has a creation date
    created = models.DateTimeField(default=timezone.now)
    # [1] Handle history as stringified JSON object
    history = models.TextField("History", default = "[]")

    def __str__(self):
        return self.code

    def full_handle(self):
        """Provide the full url of the handle, based on the current code"""

        url = "http://hdl.handle.net/{}/{}".format(self.domain, self.code)
        return url

    def add_handle(code, url, domain="21.11114", info=None):
        oErr = ErrHandle()
        obj = None
        try:
            # Check if the code is there already
            obj = TsgHandle.objects.filter(code=code).first()
            if obj == None:
                obj = TsgHandle(code=code, url=url, domain=domain)
                if info != None: obj.info = json.dumps(info)
                obj.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TsgInfo/add_handle")
            obj = None
        return obj

    def exists(code):
        obj = TsgHandle.objects.filter(code=code).first()
        return (obj != None)
