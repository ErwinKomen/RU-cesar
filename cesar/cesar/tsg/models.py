import json
from django.db import models
from django.utils import timezone
from cesar.utils import ErrHandle

MAXPARAMLEN = 100

def get_crpp_date(dtThis):
    """Convert datetime to string"""

    # Model: yyyy-MM-dd'T'HH:mm:ss
    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate

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
    # [0-1] Notes on this particular handle (if needed)
    notes = models.TextField("Notes", blank=True, null=True)

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

    def get_info(self, section = None):
        oResponse = {}
        method = "new"
        if section == None:
            oResponse['section'] = 'plain'
            oResponse['data'] = json.loads(self.info)
        else:
            lst_info = json.loads(self.info)
            section = section.lower()
            for obj_info in lst_info:
                if obj_info['type'].lower() == section:
                    if method == "old":
                        # We have the right section
                        if section == "url" or section == "inst":
                            response = "{}, {}, privs={}: {}".format(
                                 obj_info['idx'], obj_info['timestamp'], obj_info['privs'], obj_info['parsed_data'])
                        elif section == "hs_admin":
                            # Process the parsed data
                            parsed = obj_info['parsed_data']
                            lData = []
                            for k,v in parsed.items():
                                if k == "perms": 
                                    for k2, v2 in v.items():
                                        lData.append("{}={}".format(k2,v2))
                                else:
                                    lData.append("{}={}".format(k,v))
                            sData = ", ".join(lData)
                            response = "{}, idx {}, privs={}: {}".format(
                                 obj_info['timestamp'], obj_info['idx'], obj_info['privs'], sData)
                    else:
                        # Get basic information
                        oResponse['section'] = section
                        oResponse['idx'] = obj_info['idx']
                        oResponse['privs'] = obj_info['privs']
                        oResponse['timestamp'] = obj_info['timestamp']
                        if section == "url" or section == "inst":
                            oResponse['data'] = obj_info['parsed_data']
                        elif section == "hs_admin":
                            # Process the parsed data
                            parsed = obj_info['parsed_data']
                            lData = []
                            for k,v in parsed.items():
                                if k == "perms": 
                                    for k2, v2 in v.items():
                                        lData.append("{}={}".format(k2,v2))
                                else:
                                    lData.append("{}={}".format(k,v))
                            sData = ", ".join(lData)
                            oResponse['data'] = sData

                    # Now break away
                    break
        return oResponse

    def get_info_all(self):
        """Get the information from all three sections"""
        sections = ["URL", "INST", "HS_ADMIN"]
        lResponse = []
        for section in sections:
            lResponse.append(self.get_info(section))
        return lResponse

    def get_info_url(self):
        """Get the [URL] section of the information"""
        return self.get_info("URL")

    def get_info_inst(self):
        """Get the [INST] section of the information"""
        return self.get_info("INST")

    def get_info_admin(self):
        """Get the [HS_ADMIN] section of the information"""
        return self.get_info("HS_ADMIN")

    def get_history(self):
        return json.loads(self.history)
