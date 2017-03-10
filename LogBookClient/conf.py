"""
Configuration module used to set defaults for ELog connection
"""

import os
import csv
import os.path
import logging
import getpass

logger = logging.getLogger(__name__)

from six.moves import configparser


class Config(object):

    defaults = {'url'      : 'https://pswww.slac.stanford.edu/ws-auth/',
                'username' : os.environ['USER'],}
    
    keys     = ['url', 'username', 'password',
                'logbooks', 'tags']

    conf     = ['etc/pyElog.conf',
                os.path.expanduser('~/pyElog.conf'),
                os.path.expanduser('~/.pyElog.conf'), 
                os.path.expanduser('~/.pyElog.rc'),
                'pyElog.conf']

    
    def __init__(self, config=None, heading='DEFAULT'):
        self.heading = heading
        self.cf = configparser.SafeConfigParser(defaults=self.defaults)
       
        if config:
            files = self.cf.read(config)

        else: 
            files = self.cf.read(self.conf)

        for f in files:
            logger.info('Read config file %s', f)


    def get_value(self, arg):
        """
        Get a default from the config file

        Parameters
        ----------
        arg : string
            Parameter to return 

        Returns
        -------
        Config value or None
        """
        if self.cf.has_option(self.heading,arg):
            return self.cf.get(self.heading,arg)

        else:
            return None


    def get_username(self):
        """
        Get the username to be used. If not found, prompts the user
        """
        username = self.get_value('username')
        if username:
            return username
        else:
            return getpass.getuser()
    
        if self.cf.has_option(self.heading, 'username'):
            return self.cf.get(self.heading, 'username')

    
    def save(self,filename=None,heading=None,**kwargs):
        """
        Save the current configuration to a file
        
        Parameters
        ----------
        filename : string, optional
            The path to save new configuration file. By default, a hidden file
            .pyElog.conf will be created in the user home directory
        
        heading : string, optional
            Optional setting for heading

        kwargs : optional
            Any of the settings found in :attr:`.keys` can be saved in the
            configuration file upon request
        """
        if not filename:
            filename = self.conf[1]
        
        if not heading:
            heading = self.heading

        for key in self.keys:
            if key in kwargs.keys():
                if key == 'tags':
                    tags = ','.join(kwargs['tags'])
                    self.cf.set(self.heading, key, tags)

                elif key == 'logbooks':
                    area  = ','.join([book.area for book in kwargs['logbooks']])
                    name  = ','.join([book.name for book in kwargs['logbooks']])
                    self.cf.set(self.heading, 'area', area)
                    self.cf.set(self.heading, 'name', name)
                    
                else:
                    self.cf.set(heading, key, kwargs[key])

        logger.info('Saving configuration to {}'.format(filename)) 
        
        with open(filename, 'a') as f:
            self.cf.write(f)
        

 
_conf = Config()
           
