"""Models for the TSG app.

TSG is Radboud Humanities lab's technical service group.
Some of the models here serve other parts of the CESAR application.
The PidService serves the 'tsg' app within Cesar, that is for use by the TSG.

"""
import json
from django.db import models
from django.utils import timezone
import requests
from requests.auth import HTTPBasicAuth


# ========= own application
from cesar.utils import ErrHandle

MAXPARAMLEN = 100
MAX_NAME_LEN = 50
MAX_STRING_LEN = 255

def get_crpp_date(dtThis):
    """Convert datetime to string"""

    # Model: yyyy-MM-dd'T'HH:mm:ss
    sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate


# =================================== TSG MODELS ===================================================


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
    url = models.URLField("Handle URL", blank=True, null=True)
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
    # [1] Status of this handle: ini, set, chg
    status = models.CharField("Status", max_length= MAXPARAMLEN, default="ini")

    def __str__(self):
        return self.code

    def full_handle(self, plain=True):
        """Provide the full url of the handle, based on the current code"""

        sBack = ""
        if self.domain != "" and self.code != "":
            url = "https://hdl.handle.net/{}/{}".format(self.domain, self.code)
            if plain:
                sBack = url
            else:
                # Pack it into something clickable
                sBack = '<span class="badge signature gr"><a href="{}">{}</a></span>'.format(url, url)
        return sBack

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

    def get_created(self):
        sBack = self.created.strftime("%d/%b/%Y %H:%M")
        return sBack

    def get_history(self, plain=True):
        sBack = "-"
        oErr = ErrHandle()
        try:
            if plain:
                sBack = json.loads(self.history)
            else:
                lHistory = json.loads(self.history)
                if len(lHistory) > 0:
                    # Create a table myself
                    html = []
                    html.append("<table><thead><tr><th>#</th><th>occasion</th></tr></thead><tbody>")
                    for idx, hist_item in enumerate(lHistory):
                        html.append("<tr><td>{}</td><td>{}</td></tr>".format(idx+1, hist_item))
                    html.append("</tbody></table>")
                    sBack = "\n".join(html)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("tsghandle/get_history")

        return sBack

    def get_info(self, section = None):
        oResponse = None
        method = "new"
        oErr = ErrHandle()
        try:
            if section == None:
                oResponse = dict(section="plain", data=json.loads(self.info))
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
                            oResponse = dict(section=section)
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
        except:
            msg = oErr.get_error_message()
            oErr.DoError("tsghandle/get_info")
        return oResponse

    def get_info_all(self):
        """Get the information from all three sections"""

        sections = ["URL", "INST", "HS_ADMIN"]
        lResponse = []
        oErr = ErrHandle()
        try:
            for section in sections:
                oInfo = self.get_info(section)
                if not oInfo is None:
                    lResponse.append(oInfo)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("tsghandle/get_info_all")
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

    def get_info_html(self):
        """Get information in the form of HTML code"""

        sBack = "-"
        oErr = ErrHandle()
        try:
            lst_info = self.get_info_all()
            if len(lst_info) > 0:
                # Create a table myself
                html = []
                html.append('<table class="func-view"><thead><tr><th>Section</th><th>idx</th><th>Timestamp</th>')
                html.append('<th>privs</th><th>Value</th></tr></thead><tbody>')
                for idx, info_item in enumerate(lst_info):
                    html.append('<tr>')
                    html.append(' <td valign="top">{}</td>'.format(info_item.get('section')))
                    html.append(' <td valign="top">{}</td>'.format(info_item.get('idx')))
                    html.append(' <td valign="top">{}</td>'.format(info_item.get('timestamp')))
                    html.append(' <td valign="top">{}</td>'.format(info_item.get('privs')))
                    html.append(' <td valign="top">{}</td>'.format(info_item.get('data')))
                    html.append('</tr>')
                html.append('</tbody></table>')
                sBack = "\n".join(html)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("tsghandle/get_info_html")

        return sBack

    def get_status(self):
        sBack = ""
        status = self.status
        if not status is None and self.status != "":
            oStatusDict = dict(ini="Initialized", set="Handle set", chg="URL changed")
            sBack = oStatusDict.get(status, "???")
        return sBack

    def get_url(self, plain=True):
        """Show the URL this handle defines"""

        sBack = ""
        if not self.url is None:
            if plain:
                sBack = self.url
            else:
                sBack = '<span class="badge signature cl"><a href="{}">{}</a></span>'.format(self.url, self.url)
        return sBack

