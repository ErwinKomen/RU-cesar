import sys
from django.conf import settings
from django import http
from cesar.basic.models import Address

class ErrHandle:
    """Error handling"""

    # ======================= CLASS INITIALIZER ========================================
    def __init__(self):
        # Initialize a local error stack
        self.loc_errStack = []

    # ----------------------------------------------------------------------------------
    # Name :    Status
    # Goal :    Just give a status message
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def Status(self, msg):
        # Just print the message
        print(msg, file=sys.stderr)

    # ----------------------------------------------------------------------------------
    # Name :    DoError
    # Goal :    Process an error
    # History:
    # 6/apr/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def DoError(self, msg, bExit = False):
        # Append the error message to the stack we have
        self.loc_errStack.append(msg)
        # Print the error message for the user
        print("Error: "+msg+"\nSystem:", file=sys.stderr)
        # Note: exc_info gives a tuple (type, value, traceback)
        for nErr in sys.exc_info():
            if (nErr != None):
                print(nErr, file=sys.stderr)
                self.loc_errStack.append(str(nErr))
        # Is this a fatal error that requires exiting?
        if (bExit):
            sys.exit(2)
        # Otherwise: return the string that has been made
        return "<br>".join(self.loc_errStack)

    def get_error_message(self):
        arInfo = sys.exc_info()
        if len(arInfo) == 3:
            sMsg = str(arInfo[1])
            if arInfo[2] != None:
                sMsg += " at line " + str(arInfo[2].tb_lineno)
            return sMsg
        else:
            return ""

    def get_error_stack(self):
        return " ".join(self.loc_errStack)


class BlockedIpMiddleware(object):

    bot_list = ['googlebot', 'bot.htm', 'bot.com', '/petalbot', 'crawler.com', 'robot', 'crawler',
                'semrush', 'bingbot' ]
    bDebug = False

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        oErr = ErrHandle()
        if self.bDebug:
            oErr.Status("BlockedIpMiddleware: __call__")

        # First double-check if this is okay...
        response = self.process_request(request)

        if response == None:
            # No problem: we can do what we want
            # oErr.Status("Honoring request")
            response = self.get_response(request)
        else:
            oErr.Status("Denying request")

        return response

    def process_request(self, request):
        oErr = ErrHandle()

        try:
            remote_host = self.get_host(request)
            remote_ip = request.META['REMOTE_ADDR']
            path = request.path            

            if self.bDebug:
                oErr.Status("BlockedIpMiddleware: remote addr = [{}]".format(remote_ip))

            # Check for blocked IP
            if Address.is_blocked(remote_ip, request):
                # Reject this IP address
                oErr.Status("Blocked IP: {}".format(remote_ip))
                return http.HttpResponseForbidden('<h1>Forbidden</h1>')

            bHostOkay = (remote_host in settings.ALLOWED_HOSTS)
            if bHostOkay:
                # CUrrent debugging
                if self.bDebug: 
                    oErr.Status("Host: [{}]".format(remote_host))
            else:
                # Rejecting this host
                oErr.Status("Rejecting host: [{}]".format(remote_host))
                return http.HttpResponseForbidden('<h1>Forbidden</h1>')

            if remote_ip in settings.BLOCKED_IPS:
                oErr.Status("Blocking IP: {}".format(remote_ip))
                return http.HttpResponseForbidden('<h1>Forbidden</h1>')
            else:
                # Try the IP addresses the other way around
                for block_ip in settings.BLOCKED_IPS:
                    if block_ip in remote_ip:
                        oErr.Status("Blocking IP: {}".format(remote_ip))
                        return http.HttpResponseForbidden('<h1>Forbidden</h1>')
                # Get the user agent
                user_agent = request.META.get('HTTP_USER_AGENT')

                if self.bDebug:
                    oErr.Status("BlockedIpMiddleware: http user agent = [{}]".format(user_agent))

                if user_agent == None or user_agent == "":
                    # This is forbidden...
                    oErr.Status("Blocking empty user agent")
                    return http.HttpResponseForbidden('<h1>Forbidden</h1>')
                else:
                    # Check what the user agent is...
                    user_agent = user_agent.lower()
                    for bot in self.bot_list:
                        if bot in user_agent:
                            ip = request.META.get('REMOTE_ADDR')
                            # Print it for logging
                            msg = "blocking bot: [{}] {}: {}".format(ip, bot, user_agent)
                            print(msg, file=sys.stderr)
                            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
        except:
            msg = oErr.get_error_message()
            oErr.DoError("BlockedIpMiddleware/process_request")
        return None

    def get_host(self, request):
        """
        Return the HTTP host using the environment or request headers. Skip
        allowed hosts protection, so may return an insecure host.
        """
        # We try three options, in order of decreasing preference.
        if settings.USE_X_FORWARDED_HOST and (
                'HTTP_X_FORWARDED_HOST' in self.META):
            host = request.META['HTTP_X_FORWARDED_HOST']
        elif 'HTTP_HOST' in request.META:
            host = request.META['HTTP_HOST']
        else:
            # Reconstruct the host, taking the part before a possible colon
            host = request.META['SERVER_NAME']

        # Strip off any colon
        host = host.split(":")[0]
        return host

    def get_port(self, request):
        """Return the port number for the request as a string."""
        if settings.USE_X_FORWARDED_PORT and 'HTTP_X_FORWARDED_PORT' in request.META:
            port = request.META['HTTP_X_FORWARDED_PORT']
        else:
            port = request.META['SERVER_PORT']
        return str(port)


