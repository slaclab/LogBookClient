'''
When using requests to talk to web services and authenticaing with Kerberos, use this ticket to generate the appropriate Kerberos headers
For example create a ticket like so
   self.krbheaders = KerberosTicket("HTTP@" + urlparse(self.questionnaire_url).hostname).getAuthHeaders()
Then when making a call using requests, pass the headers as follows. 
   r = requests.get(self.questionnaire_url + "ws/questionnaire/get_enum_field_names", headers=self.krbheaders)
'''

import kerberos

class KerberosTicket:
    def __init__(self, service):
        __, krb_context = kerberos.authGSSClientInit(service)
        kerberos.authGSSClientStep(krb_context, "")
        self._krb_context = krb_context
        self.auth_header = ("Negotiate " + kerberos.authGSSClientResponse(krb_context))

    def verify_response(self, auth_header):
        # Handle comma-separated lists of authentication fields
        for field in auth_header.split(","):
            kind, __, details = field.strip().partition(" ")
            if kind.lower() == "negotiate":
                auth_details = details.strip()
                break
        else:
            raise ValueError("Negotiate not found in %s" % auth_header)
        # Finish the Kerberos handshake
        krb_context = self._krb_context
        if krb_context is None:
            raise RuntimeError("Ticket already used for verification")
        self._krb_context = None
        kerberos.authGSSClientStep(krb_context, auth_details)
        kerberos.authGSSClientClean(krb_context)

    def getAuthHeaders(self):
        return {"Authorization": self.auth_header}

