#!/usr/bin/env python

import logging
import argparse
import getpass
import json
from urlparse import urlparse
import requests
from kerbticket import KerberosTicket

logger = logging.getLogger(__name__)

class Column(object):

    def __init__ (self, table, coldef):
        self._table  = table
        self._coldef = coldef

    def id     (self): return int(self._coldef['id'])
    def name   (self): return     self._coldef['name']
    def type   (self): return     self._coldef['type']
    def source (self): return     self._coldef['source']

    def is_editable (self): return bool(self._coldef['is_editable'])

    def position (self): return int(self._coldef['position'])

class Table(object):

    def __init__ (self, runtables, config, exper_id):
        self._runtables = runtables
        self._config    = config
        self._exper_id  = exper_id

    def id    (self): return int(self._config['id'])
    def name  (self): return     self._config['name']
    def descr (self): return     self._config['descr']
    
    def modified_time (self): return self._config['modified_time']
    def modified_uid  (self): return self._config['modified_uid']
    
    def columns (self) : return [Column(self, cd) for cd in self._config['coldef']]

    def values(self, fromrun, throughrun=None):
        r_json = self._get_row(fromrun, throughrun)
        #result = dict()
        return {'runs': r_json['runs'], 'last_run': r_json['last_run']}

    def _get_row(self, fromrun, throughrun=None):
        if throughrun is None: throughrun = fromrun
        params = {
            'exper_id':    self._exper_id ,
            'table_id':    self.id() ,
            'from_run':    fromrun ,
            'through_run': throughrun
        }
        return self._runtables._get('DataPortal/runtable_user_table_get.php', params)

    def setValue(self, runnum, param, value):

        for column in self.columns():

            # find the column and make sure it's editable
            if column.name() == param:
                if not column.is_editable():
                    raise ValueError("parameter '%s' can't be modified" % param)

                # fetch the whole row because the result also has the run identity
                #
                # TODO: Perhaps teh cell modification algorithm should be
                #       extended to support run numbers in addition to
                #       identifiers.

                params = {
                    'exper_id': self._exper_id ,
                    'table_id': self.id() ,
                    'cells':    json.dumps([{
                        'run_id':    self._get_row(runnum)['run2id']["%d" % runnum] ,
                        'coldef_id': column.id() ,
                        'value':     value
                    },])
                }
                self._runtables._post('DataPortal/runtable_user_cell_save.php', params)
                return

        raise ValueError("unknown parameter '%s'" % param)

class RunTables(object):

    """Connection manager to the Web Server."""
    
    #####################################################################################

    def __init__ (self, *p, **kw):
        self._conn_params = dict()
        self._conn_params['webServiceURL']      = None
        self._conn_params['userID']     = None
        self._conn_params['password'] = None
        for key in self._conn_params:
            if key in kw:
                self._conn_params[key] = kw[key]

   #####################################################################################

    def usertables (self, *p, **kw):

        if 'exper_id' in kw:
            exper_id = kw['exper_id']
        else:
            if 'exper_name' in kw:
                exper_id = self._get_exper_id(kw['exper_name'])
            else:
                raise ValueError("no experiment identity found among the parameters of the method")

        tables_json = self._get('DataPortal/runtable_user_tables.php', {'exper_id':exper_id})
        tables_data = tables_json['table_data']

        return [ Table(self, tables_data[tid]['config'], exper_id) for tid in tables_data ]


    def findUserTable (self, *p, **kw):

        if 'table_id' in kw:
            table_id   = kw['table_id']
            table_name = None
        else:
            if 'table_name' in kw:
                table_id   = None
                table_name = kw['table_name']
            else:
                raise ValueError("no table identity found among the parameters of the method")
                    
        for table in self.usertables(*p, **kw):
            if table_id is None:
                if table.name() == table_name: return table
            else:
                if table.id() == table_id: return table

        return None

   #####################################################################################
 
    def _get_exper_id(self, exper_name):
        r_json = self._get('DataPortal/experiment_info.php', {'name':exper_name})
        return int(r_json['id'])

    def _request(self, method, uri, params={}):
        
        url =  "%s/%s" % (self._conn_params['webServiceURL'], uri)
        r_args = { 'url' : url }

        if 'password' in self._conn_params and self._conn_params['password']:
            r_args['auth'] = requests.auth.HTTPBasicAuth(self._conn_params['userID'], self._conn_params['password'])
        else:
            r_args['headers'] = KerberosTicket("HTTP@" + urlparse(url).hostname).getAuthHeaders()

        logger.debug("Making a call to %s", r_args['url'])

        if   method == 'GET':  
            r_args['params'] = params
            r = requests.get(**r_args)
        elif method == 'POST': 
            r_args['data'] = params
            r = requests.post(**r_args)
        else:
            raise ValueError("unsupported HTTP method '%s'" % method)

        if r.status_code != 200:
            raise Exception("the request to %s failed with HTTP status code %d" % (r_args['url'],r.status_code))
        
        r_json = r.json()
        logger.debug("JSON response %s", r.text)
        if r_json['status'] != 'success':
            raise Exception("service %s reported error status %s" % (r_args['url'],r_json['message']))

        return r_json

    def _get (self, uri, params={}): return self._request('GET',  uri, params)
    def _post(self, uri, params={}): return self._request('POST', uri, params)



if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='Manage User Run tables')
    parser.add_argument("--url", help="Web server URL - is using kerberos, use something like https://pswww.slac.stanford.edu/ws-kerb; else use https://pswww.slac.stanford.edu/ws-auth ", required=True)
    parser.add_argument('--experiment', help="The name of the experiment, for example, diadaq13", required=True)
    parser.add_argument('--user', help="UserID used for the connection", default=getpass.getuser())
    parser.add_argument('--password', help="Password; if not specified, we use kerberos")
    parser.add_argument('-v', '--verbose', help="Turn on verbose logging", action='store_true');
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    r = RunTables(webServiceURL=args.url, userID=args.user, password=args.password);
    for t in r.usertables(exper_name=args.experiment):
        print "Table ", t.name()
        for c in t.columns():
            print c.name()
        searched_t = r.findUserTable(exper_name=args.experiment, table_name=t.name())
        print "Searched Table:", searched_t.name()
