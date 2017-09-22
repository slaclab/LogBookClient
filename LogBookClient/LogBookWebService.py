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

import httplib
import mimetools
import mimetypes
import pwd
import simplejson
import socket
import stat
import tempfile
from urlparse import urlparse


#import tkMessageBox
#from Tkinter import *
#from ScrolledText import *

import requests
from requests.auth import HTTPBasicAuth

from kerbticket import KerberosTicket
 
#----------------------------------


def __get_auth_params(ws_url=None, user=None, passwd=None):
    suffix = ws_url.rsplit('-',1)[-1]
    authParams = {}
    if passwd:
        authParams['auth']=HTTPBasicAuth(user, passwd)
    else:
        if suffix == 'kerb':
            authParams['headers']=KerberosTicket("HTTP@" + urlparse(ws_url).hostname).getAuthHeaders()
    return authParams


def ws_get_experiments (experiment=None, instrument=None, ws_url=None, user=None, passwd=None):

    # Try both experiments (at instruments) and facilities (at locations)
    #
    urls = [ ws_url+'/LogBook/RequestExperimentsNew.php?instr='+instrument+'&access=post',
             ws_url+'/LogBook/RequestExperimentsNew.php?instr='+instrument+'&access=post&is_location' ]

    try:
        d = dict()
        authParams = __get_auth_params(ws_url, user, passwd) 
        
        for url in urls:
            result = requests.get(url, **authParams).json()
            
            if len(result) <= 0:
                print "ERROR: no experiments are registered for instrument: %s" % instrument

            # if the experiment was explicitly requested in the command line then try to find
            # the one. Otherwise return the whole list
            #
            if experiment is not None:
                for e in result['ResultSet']['Result']:
                    if experiment == e['name']:
                        d[experiment] = e
                        d[experiment]['tags'] = ws_get_tags(e['id'], ws_url, user, passwd)
            else:
                for e in result['ResultSet']['Result']:
                    d[e['name']] = e
                    d[e['name']] = ws_get_tags(e['id'], ws_url, user, passwd)
        return d

    except requests.exceptions.RequestException as e:
        print "ERROR: failed to get a list of experiment from Web Service due to: ", e
        sys.exit(1)

#----------------------------------

def ws_get_current_experiment (instrument, station, ws_url, user, passwd):

    url = ws_url+'/LogBook/RequestCurrentExperiment.php?instr='+instrument
    if station != '' : url += '&station='+station

    authParams = __get_auth_params(ws_url, user, passwd) 

    try:
        result   = requests.get(url, **authParams).json()
        if len(result) <= 0:
            print "ERROR: no experiments are registered for instrument:station %s:%s" % (instrument,station)

        #print 'result:', result 
        e = result['ResultSet']['Result']
        if e is not None:
            return e['name']

        print "ERROR: no current experiment configured for this instrument:station %s:%s" % (instrument,station)
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print "ERROR: failed to get the current experiment info from Web Service due to: ", e
        sys.exit(1)

#----------------------------------

def ws_get_tags (id, ws_url, user, passwd):

    url = ws_url+'/LogBook/RequestUsedTagsAndAuthors.php?id='+id;

    authParams = __get_auth_params(ws_url, user, passwd) 


    try:
        result = requests.get(url, **authParams).json()
        if result['Status'] != 'success':
            print "ERROR: failed to obtain tags for experiment id=%d because of:" % id,result['Message']
            sys.exit(1)

        #print 'Tags:', result['Tags']
        return result['Tags']

    except requests.exceptions.RequestException as e:
        print "ERROR: failed to get the current experiment info from Web Service due to: ", e

#----------------------------------
#(inst='AMO', exp='amodaq14', run='825', tag='TAG1',
# msg='EMPTY MESSAGE', fname=None, fname_att=None, resp=None) :

def submit_msg_to_elog(ws_url, usr, passwd, ins, sta, exp, cmd, logbook_experiments, lst_tag=[''], run='', msg_id='', msg='', lst_descr=[''], lst_fname=['']):

    exper_id = logbook_experiments[exp]['id']

    url = ws_url+'/LogBook/NewFFEntry4grabberJSON.php'

    child_output = ''
    if cmd is not None: child_output = os.popen(cmd).read()

    if (run != '') and (msg_id != '') :
        print 'run', run
        print 'message_id', msg_id

        msg = "\nInconsistent input:" \
            + "\nRun number can't be used togher with the parent message ID." \
            + "\nChoose the right context to post the screenshot and try again." 
        print msg
        return

    params = {}
    params['author_account']  = usr
    params['id']              = exper_id
    params['message_text']    =  msg
    params['text4child']      = child_output
    #params['instrument']      = ins
    #params['experiment']      = exp

    if run != '' :
        params['scope']   = 'run'
        params['run_num'] = run

    elif msg_id != '' : 
        params['scope']      = 'message'
        params['message_id'] = msg_id

    else:
        params['scope'] =  'experiment'

    if lst_tag !=[''] :
        params['num_tags'] = str(len(lst_tag))
        for i,tag in enumerate(lst_tag) :
            s = '%d' % (i)
            params['tag_name_'  + s] = tag
            params['tag_value_' + s]  = ''

    files = {}
    if lst_fname != [''] :
        for i,(fname, descr) in enumerate( zip(lst_fname, lst_descr) ) :
            s = '%d' % (i+1)
            #params.append(MultipartParam.from_file('file' + s, fname))
            files['file' + s]  =  open(fname, 'rb')
            params['file' + s] = descr

#!!!!!!!!!!!!!!!!!!!!!!!
#    print 'params:', params
#    return {'status': 'error', 'message': 'Bad Error message'}
#    return {'status': 'success', 'message_id': '123456'}
#!!!!!!!!!!!!!!!!!!!!!!!
    


    try:
        authParams = __get_auth_params(ws_url, usr, passwd) 

        #print 'Try to submit message: \nurl: ', url, '\ndatagen:', datagen, '\nheaders:' , headers
        post_result = requests.post(url, data=params, files=files, **authParams)
        #print "Result of post is", post_result.text
        result = post_result.json()

        #print 'result:',    result
        #NORMAL: result: {'status': 'success', 'message_id': '125263'}
        #ERROR:  result: {'status': 'error', 'message': 'Run number 285 has not been found. Allowed range of runs is: 2..826.'}

        if result['status'] == 'success':
            print 'New message ID:', result['message_id']
        #else :
        #    print 'Error:', result['message']

        return result

    except requests.exceptions.RequestException as e:
        print "ERROR: failed to get the current experiment info from Web Service due to: ", e

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
            print "No instrument name found among command line parameters"
            sys.exit(3)

        if self.url is None:
            print "No web service URL found among command line parameters"
            sys.exit(3)

        if self.usr is None:
            self.usr = pwd.getpwuid(os.geteuid())[0]
            print "User login name is not found among command line parameters" +\
                  "\nTry to gess that the user name is " + self.usr

        self.set_experiment(exp)



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

        print 'Set experiment:', self.exp

        # ------------------------------------------------------
        # Get a list of experiments for the specified instrument
        # and if a specific experiment was requested make sure
        # the one is in the list.
        # ------------------------------------------------------

        self.logbook_experiments = ws_get_experiments (self.exp, self.ins, self.url, self.usr, self.pas)


    def get_list_of_tags(self) :

        if self.logbook_experiments == {} :
            print '\nWARNING! ws_get_experiments(exp,ins,url) '\
                  'returns empty dictionary for\nexp: %s\nins: %s\nurl: %s' % (self.exp, self.ins, self.url)

        try : list_raw = self.logbook_experiments[self.exp]['tags']
        except KeyError, reason:
            print '\nWARNING! List of tags is not found for exp %s due to: %s' % (self.exp, reason)
            return []

        list_str = []
        for tag in list_raw :
            list_str.append(str(tag))
        return list_str


    def get_list_of_experiments(self) :
        d = ws_get_experiments (None, self.ins, self.url, self.usr, self.pas)
        return d.keys()


    def get_current_experiment(self) :
        return ws_get_current_experiment (self.ins, self.sta, self.url, self.usr, self.pas)


    def post(self, msg='', run='', res='', tag='', des='', att='') :
        result = submit_msg_to_elog(self.url, self.usr, self.pas, self.ins, self.sta, self.exp, self.cmd, self.logbook_experiments, \
                                    msg=msg, run=run, msg_id=res, lst_tag=[tag], lst_descr=[des], lst_fname=[att])
        return  result
        #NORMAL: result: {'status': 'success', 'message_id': '125263'}
        #ERROR:  result: {'status': 'error', 'message': 'Run number 285 has not been found. Allowed range of runs is: 2..826.'}

    def post_lists(self, msg='', run='', res='', lst_tag=[''], lst_des=[''], lst_att=['']) :
        result = submit_msg_to_elog(self.url, self.usr, self.pas, self.ins, self.sta, self.exp, self.cmd, self.logbook_experiments, \
                                    msg=msg, run=run, msg_id=res, lst_tag=lst_tag, lst_descr=lst_des, lst_fname=lst_att)
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

    print 50*'='+'\nStart grabber for ELog with input parameters:'
    for k,v in pars.items():
        print '%9s : %s' % (k,v)

    print 50*'='+'\nTest LogBookWebService(**pars) methods:\n'

    lbws = LogBookWebService(**pars)
    print '\nTest lbws.logbook_experiments:\n',     lbws.logbook_experiments
    print '\nTest lbws.get_list_of_experiments():', lbws.get_list_of_experiments()
    print '\nselflbws.get_list_of_tags():',         lbws.get_list_of_tags()

    print 50*'='+'\nTest global WebService methods:'
    print '\nTest ws_get_experiments(exp, ins, url):\n', ws_get_experiments (experiment=None, instrument=ins, ws_url=url, user=usr, passwd=pas)
    print '\nTest ws_get_current_experiment(ins, sta, url): ', ws_get_current_experiment (ins, sta, url, usr, pas)
    #print '\nTest ws_get_tags(id, url):\n', ws_get_tags ('409', url)

    print 50*'='+'\nSuccess!'
    
    sys.exit('End of test_LogBookWebService.')


#-----------------------------
if __name__ == "__main__" :

    test_LogBookWebService()

#-----------------------------
