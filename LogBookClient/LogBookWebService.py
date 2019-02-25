#--------------------------------------------------------------------------
# Description:
#   LogBookWebService.py
#------------------------------------------------------------------------
"""Web service for LogBookGrabber_qt.py

This software was developed for the SIT project.  If you use all or
part of it, please give an appropriate acknowledgment.

@see LogBookGrabber_qt.py

@version $Id: LogBookWebService.py 12833 2016-11-03 22:16:27Z trendahl@SLAC.STANFORD.EDU $

@author Mikhail S. Dubrovin
"""

#--------------------------------
#  Imports of standard modules --
#--------------------------------
import sys
import os

#-----------------------------
# Imports for other modules --
#-----------------------------
#import sys
#import os
import os.path

import http.client
import mimetypes
import pwd
import simplejson
import socket
import stat
import tempfile
from urllib.parse import urlparse
import getpass

#import tkMessageBox
#from Tkinter import *
#from ScrolledText import *

import requests
from requests.auth import HTTPBasicAuth


#----------------------------------


def __get_auth_params(ws_url=None, user=None, passwd=None):
    suffix = ws_url.rsplit('-',1)[-1]
    authParams = {}
    if passwd:
        authParams['auth']=HTTPBasicAuth(user, passwd)
    else:
        from .kerbticket import KerberosTicket
        if suffix == 'kerb':
            authParams['headers']=KerberosTicket("HTTP@" + urlparse(ws_url).hostname).getAuthHeaders()
    return authParams


def ws_get_experiments (experiment=None, instrument=None, ws_url=None, user=None, passwd=None):

    # Try both experiments (at instruments) and facilities (at locations)
    #
    urls = [ ws_url+'/lgbk/ws/postable_experiments' ]

    try:
        d = dict()
        authParams = __get_auth_params(ws_url, user, passwd)

        for url in urls:
            result = requests.get(url, **authParams).json()

            if len(result) <= 0:
                print("ERROR: no experiments are registered for instrument: %s" % instrument)

            # if the experiment was explicitly requested in the command line then try to find
            # the one. Otherwise return the whole list
            #
            if experiment is not None:
                for e in result['value']:
                    if experiment == e['name']:
                        d[experiment] = e
            else:
                for e in result['value']:
                    if e['instrument'] in [ instrument, 'NEH' ]:
                        d[e['name']] = e
        return d

    except requests.exceptions.RequestException as e:
        print("ERROR: failed to get a list of experiment from Web Service due to: ", e)
        sys.exit(1)

#----------------------------------

def ws_get_current_experiment (instrument, station, ws_url, user, passwd):

    url = ws_url+'/lgbk/ws/activeexperiments'

    authParams = __get_auth_params(ws_url, user, passwd)
    print("Looking for current experiment on instrument {} station {}".format(instrument, station))

    try:
        result = requests.get(url, **authParams).json()
        for e in result['value']:
            if e['instrument'] == instrument:
                if station:
                    if str(station) == str(e["station"]):
                        return e['name']
                else:
                    return e['name']

        print("ERROR: no current experiment configured for this instrument:station %s:%s" % (instrument,station))
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print("ERROR: failed to get the current experiment info from Web Service due to: ", e)
        sys.exit(1)

#----------------------------------

def ws_get_tags (expname, ws_url, user, passwd):

    url = ws_url+'/lgbk/' + expname + '/ws/get_elog_tags';

    authParams = __get_auth_params(ws_url, user, passwd)


    try:
        result = requests.get(url, **authParams).json()
        return result['value']

    except requests.exceptions.RequestException as e:
        print("ERROR: failed to get the current experiment info from Web Service due to: ", e)

#----------------------------------
#(inst='AMO', exp='amodaq14', run='825', tag='TAG1',
# msg='EMPTY MESSAGE', fname=None, fname_att=None, resp=None) :

def submit_msg_to_elog(ws_url, usr, passwd, ins, sta, exp, cmd, logbook_experiments, lst_tag=None, run_num='', msg_id='', msg='', lst_fname=[''], emails=None):

    exper_name = logbook_experiments[exp]['name']
    if (run_num != '') and (msg_id != '') :
        print('run', run)
        print('message_id', msg_id)

        msg = "\nInconsistent input:" \
            + "\nRun number can't be used togher with the parent message ID." \
            + "\nChoose the right context to post the screenshot and try again."
        print(msg)
        return


    serverURL = "{0}/lgbk/{1}/ws/new_elog_entry".format(ws_url, exper_name)
    payload = { 'log_text': msg }
    if run_num != '':
        payload['run_num'] = run_num
    if emails and emails != '':
        payload['log_emails'] = emails
    if msg_id and msg_id != '':
        payload['parent'] = msg_id
    if lst_tag and lst_tag[0] != '':
        payload['log_tags'] = " ".join(lst_tag)

    files = []
    if lst_fname != [''] :
        files = [("files",  (os.path.basename(fname), open(fname, 'rb'), mimetypes.guess_type(fname)[0])) for fname in lst_fname ]
        print(files)

    try:
        authParams = __get_auth_params(ws_url, usr, passwd)

        #print 'Try to submit message: \nurl: ', url, '\ndatagen:', datagen, '\nheaders:' , headers
        post_result = requests.post(serverURL, data=payload, files=files, **authParams)
        post_result.raise_for_status()
        #print "Result of post is", post_result.text
        result = post_result.json()

        #print 'result:',    result
        #NORMAL: result: {'status': 'success', 'message_id': '125263'}
        #ERROR:  result: {'status': 'error', 'message': 'Run number 285 has not been found. Allowed range of runs is: 2..826.'}

        if result['success']:
            print('Server response %s' % result )
        #else :
        #    print 'Error:', result['message']

        return result

    except requests.exceptions.RequestException as e:
        print("ERROR: failed to generate a new elog entry due to: ", e)
        return {"success": False, "message": str(e)}

#----------------------------------
#----------------------------------
#----------------------------------
#----------------------------------

class LogBookWebService :

    #def __init__(self, ins='AMO', sta='', exp='amodaq14', url='https://cdlx27.slac.stanford.edu/ws-auth', usr='amoopr', pas=None) :
    def __init__(self, ins=None, sta=None, exp=None, url=None, usr=None, pas=None, cmd=None) :
        self.ins = ins
        self.sta = sta
        self.exp = exp
        self.url = url
        self.usr = usr
        self.pas = pas
        self.cmd = cmd

        if self.ins is None:
            print("No instrument name found among command line parameters")
            sys.exit(3)

        if self.url is None:
            print("No web service URL found among command line parameters")
            sys.exit(3)

        if self.usr is None:
            self.usr = pwd.getpwuid(os.geteuid())[0]
            print("User login name is not found among command line parameters" +\
                  "\nTry to gess that the user name is " + self.usr)

        self.set_experiment(exp)

        mimetypes.init()



    def set_experiment(self, exp) :
        #print 'Try to set experiment: ' + exp

        # ---------------------------------------------------------
        # If the current experiment was requested then check what's
        # (if any) the current experiment for the instrument.
        # ---------------------------------------------------------

        if exp is not None:
            if exp == 'current':
                self.exp = ws_get_current_experiment (self.ins, self.sta, self.url, self.usr, self.pas)
            else :
                self.exp = exp

        print('Set experiment:', self.exp)

        # ------------------------------------------------------
        # Get a list of experiments for the specified instrument
        # and if a specific experiment was requested make sure
        # the one is in the list.
        # ------------------------------------------------------

        self.logbook_experiments = ws_get_experiments (self.exp, self.ins, self.url, self.usr, self.pas)


    def get_list_of_tags(self) :



        try : list_raw = ws_get_tags(self.exp, self.url, self.usr, self.pas)
        except Exception as reason:
            print('\nWARNING! List of tags is not found for exp %s due to: %s' % (self.exp, reason))
            return []

        list_str = []
        for tag in list_raw :
            list_str.append(str(tag))
        return list_str


    def get_list_of_experiments(self) :
        d = ws_get_experiments (None, self.ins, self.url, self.usr, self.pas)
        return list(d.keys())


    def get_current_experiment(self) :
        return ws_get_current_experiment (self.ins, self.sta, self.url, self.usr, self.pas)


    def post(self, msg='', run='', res='', tag='', att='') :
        result = submit_msg_to_elog(self.url, self.usr, self.pas, self.ins, self.sta, self.exp, self.cmd, self.logbook_experiments, \
                                    msg=msg, run_num=run, msg_id=res, lst_tag=[tag], lst_fname=[att])
        return  result
        #NORMAL: result: {'status': 'success', 'message_id': '125263'}
        #ERROR:  result: {'status': 'error', 'message': 'Run number 285 has not been found. Allowed range of runs is: 2..826.'}

    def post_lists(self, msg='', run='', res='', lst_tag=[''], lst_att=['']) :
        result = submit_msg_to_elog(self.url, self.usr, self.pas, self.ins, self.sta, self.exp, self.cmd, self.logbook_experiments, \
                                    msg=msg, run_num=run, msg_id=res, lst_tag=lst_tag, lst_fname=lst_att)
        return result


#----------------------------------
#----------------------------------
#---------     TESTS   ------------
#----------------------------------
#----------------------------------

def test_LogBookWebService() :

    ins = 'AMO'
    sta = '0'
    exp = 'amodaq14'
    usr = 'amoopr'
    url = 'https://pswww-dev.slac.stanford.edu/ws-auth'
    pas = 'password'
    cmd = ''

    pars = {
            'ins' : ins,
            'sta' : sta,
            'exp' : exp,
            'url' : url,
            'usr' : usr,
            'pas' : pas,
            'cmd' : cmd
            }

    print(50*'='+'\nStart grabber for ELog with input parameters:')
    for k,v in list(pars.items()):
        print('%9s : %s' % (k,v))

    print(50*'='+'\nTest LogBookWebService(**pars) methods:\n')

    lbws = LogBookWebService(**pars)
    print('\nTest lbws.logbook_experiments:\n',     lbws.logbook_experiments)
    print('\nTest lbws.get_list_of_experiments():', lbws.get_list_of_experiments())
    print('\nselflbws.get_list_of_tags():',         lbws.get_list_of_tags())

    print(50*'='+'\nTest global WebService methods:')
    print('\nTest ws_get_experiments(exp, ins, url):\n', ws_get_experiments (experiment=None, instrument=ins, ws_url=url, user=usr, passwd=pas))
    print('\nTest ws_get_current_experiment(ins, sta, url): ', ws_get_current_experiment (ins, sta, url, usr, pas))
    #print '\nTest ws_get_tags(id, url):\n', ws_get_tags ('409', url)

    print(50*'='+'\nSuccess!')

    sys.exit('End of test_LogBookWebService.')


#-----------------------------
if __name__ == "__main__" :

    test_LogBookWebService()

#-----------------------------
