######################
# Standard Packages --
######################
import logging

logger = logging.getLogger(__name__)

import io
import os
import csv
from getpass    import getpass
from simplejson import JSONDecodeError

##########################
# Non-Standard Packages --
##########################
import six                   #Useful if we ever got to Python 3.x
from .conf             import _conf, Config
from .datatypes        import Logbook, LogEntry, Tag, Attachment
from .utils            import get_text_from_editor
from LogBookWebService import LogBookWebService


class ElogClient(object):
    """
    Client interface to the Elog
    
    Parameters
    ----------
    username : string, optional
        The username for authentification

    password : string, optional
        The password for authentificiation
    
    config : string, optional
        A file path to load a saved configuration from. By default, the users
        home area will be searched.
    
    heading : string, optional
        A configuration file can save multiple headers to store different Elog
        configurations. You can specify which one to using this keyword. 
    
    ask : bool, optional
        If True, the password will be requested via getpass
    
    Attributes
    ----------
    tags : list
        A list of all tags associated with the client

    logbooks : list
        A list of all logbooks assoicated with the client
    """

    _url  = "https://pswww.slac.stanford.edu/ws-auth"

    
    def __init__(self, username=None, password=None, ask=True, config=None, heading='DEFAULT'):
        
        #Load Configuration
        if config: 
            self._conf = Config(config=config, heading=heading)

        else:
            self._conf = _conf
        
        #Load Authorization Information
        if not username:
            username = self._conf.get_username()

        if not password:
            password = self._conf.get_value('password')
        

        if username and not password and ask:
            password = getpass('Elog Password (username={}):'
                               .format(username))
        
        if self._conf.get_value('url'):
            self._url = self._conf.get_value('url')

        logger.info('Using base URL %s', self._url)
        
        if username and password:
            logger.info('Using username %s for authentication.',
                        username)

            self._auth = (username,password)

        else:
            logger.info('No authentication configured.')
            self._auth = None
        
        #Load cached tags and logbooks
        self.tags     = []
        self.logbooks = []
        
        tags = self._conf.get_value('tags')
        
        if tags:
           for group in csv.reader([tags]):
               [self.create_tag(tag) for tag in group]
        
        #Kind of an ugly way to do this.
        #Read two lists and zip together
        areas = self._conf.get_value('area')  
        if areas:
            names = [groups for groups in csv.reader([self._conf.get_value('name')])]
            for i,group in enumerate(csv.reader([areas])):
                for j, area in enumerate(group):
                    
                    try:
                         self.logbooks.append(Logbook(area,names[i][j])) 
                    except IndexError:                            
                        raise EnvironmentError('Configuration has uneven '\
                                               'amount of cached Logbook '\
                                               'information.')


    def create_tag(self, text, active=True):
        """
        Create a tag to be associated with the Client

        Parameters
        ----------
        text : string
            text of the tag

        active : bool , optional
            Active state of the tag. True by default.
        
        Returns
        -------
        :class:`.Tag` object
        """
        tag = Tag(text,active=active)
        
        if tag not in self.tags:
            self.tags.append(tag)
            return tag

        logger.warning('Tag {} already exists'.format(text))
        return self.tags[self.tags.index(tag)]
    

    @property
    def active_tags(self):
        """
        A list of active tags associated with Elog Client
        """
        return [tag.name for tag in self.tags if tag.active]
   
 
    def activate_tag(self, text, active=True):
        """
        Change the active state of a previously loaded tag
        
        Parameters
        ----------
        text : string
            The text of the tag

        active: bool, optional
            The desired active state for the tag.
        
        Raises
        ------
        ValueError
            Raised if tag has not previously been loaded
        """
        tag = Tag(tag)

        if tag not in self.tags:
            raise ValueError('Tag {} has not been created'.format(tag))
            
        self.tags[self.tags.index(tag)].active = active
       
 
    @property
    def previous_tags(self):
        """
        A list of previously used tags in Logbook instances
        
        .. note::
            These do not count as loaded tags for the client, so they must be
            instantiated with the :meth:`.create_tag` before being activated
        """
        tags = []
        for book in self.logbooks:
            tags.extend(self._logbook_service(book).get_list_of_tags())
        return tags
    
    
    def add_logbook(self, hutch, facilities=False,
                       experiment=None, active=True):
        """
        Instantiate a Logbook instance for the client

        Parameters
        ----------
        hutch : string
            The three letter acronym for the Experimental Area, capitalization
            optional

        facilities : bool, optional
            If you would like to use a facilities Elog set this True.
            Otherwise, it is assumed that you want to use the current
            experimental Elog. If you select this option, leave the experiment
            keyword blank.

        experiment : string, optional
            The choice of experimental Elog to use. By default, the current
            experiment is used.
        
        active: bool, optional
            The desired active state for the Logbook.

        Returns
        -------
        :class:`.Logbook`
            A Logbook object representing the desired Elog 
        """
        hutch = hutch.upper().strip()
        
        if experiment and facilities:
            experiment = None

        if facilities:
            area = 'NEH'
            name = '{} Instrument'.format(hutch)

        else:
            area = hutch
            name = experiment
        
        logbook = Logbook(area, name=name, active=active)
        
        if logbook not in self.logbooks:
            self.logbooks.append(logbook)
            return logbook

        logger.warning('Logbook {} already exists'.format(logbook))
        return self.logbooks[self.logbooks.index(logbook)] 
    
   
    @property
    def active_logbooks(self):
        """
        List of currently active logbooks
        """
        return [book for book in self.logbooks if book.active]

    
    def activate_logbook(self, hutch, active=True, facilities=False, experiment=None):
        """
        Activate a Logbook that has already been instantiated with :meth:`.add_logbook`

        Parameters
        ----------
        hutch : string
            The three letter acronym for the Experimental Area, capitalization
            optional
        
        active : bool
            Choice to activate logbook or deactivate

        facilities : bool, optional
            If you would like to use a facilities Elog set this True.
            Otherwise, it is assumed that you want to use the current
            experimental Elog. If you select this option, leave the experiment
            keyword blank.

        experiment : string, optional
            The choice of experimental Elog to use. By default, the current
            experiment is used.
        """
        hutch = hutch.upper().strip()
        
        if experiment and facilities:
            experiment = None

        if facilities:
            area = 'NEH'
            name = '{} Instrument'.format(hutch)

        else:
            area = hutch
            name = experiment
        
        logbook = Logbook(area, name=name, active=active)
        
        if logbook not in self.logbooks:
            raise ValueError('Logbook {} has not been created'.format(logbooks))
            
        self.logbooks[self.logbooks.index(logbook)].active = active


    def post(self, text,  tags = None, 
             attachments = None, run = None,
             verify = False,):
        """
        Create a log entry
        
        The entry will automatically be posted to all of the active logbooks in
        the client. You can check which will are active by looking at
        :attr:`.active_logbooks`. In addition, if the tags keyword is set to
        None, all of the active tags will be used as well. These can be checked
        by looking at the :attr:`.active_tags`. 
        
        Parameters
        ----------
        text : string
            The body of the entry

        tags : string or list of strings, optional
            The tags to use for the logbook post. If tags are provided the
            :attr:`.active_tags` will be ignored
       
        attachments: file names, or list of file names or Attachment objects
            The attachments to add to the log entry, 
        
        run : string, int
            Run number associated with Elog post
        
        verify : bool
            Check that the tags already exist, if not raise an Error
        
        
        Returns
        -------
        dict
            Dictionary of created LogEntry attributes
        
        Raises
        ------
        ValueError
            If the logbook does not exist, or an invalid attachment is given
        """
        #Convert single values to lists
        if tags:
            if isinstance(tags,six.string_types):
                tags = [tags]
        else:
            tags = self.active_tags

        if attachments:
            if isinstance(attachments,(Attachment,six.string_types)):
                attachments = [attachments]
        
        #Check tags
        if tags:
            if verify:
                for tag in tags:
                    if (tag not in self.previous_tags and \
                        tag not in self.active_tags):
                        raise ValueError('Tag {} has not been '\
                                         'created before'.format(tag))
                            
            tags = [Tag(tag) for tag in tags]
        
        #Check attachments
        toattach = []
        if attachments:
            for a in attachments:
                
                if isinstance(a, Attachment):
                    toattach.append(a)
            
                elif isinstance(a, six.stringtypes):

                    toattach.append(Attachment(a))

                else:
                    raise ValueError('Attachments must be file names or '\
                                     'Elog Attachment objects')
        
        logbooks = self.active_logbooks 
        
        if not logbooks:
            raise ValueError("Must have at least one active logbook to post")

        #Create Post
        log = LogEntry(text, logbooks=logbooks, author=self._auth[0],
                       tags=tags, run=run , attachments=toattach)
        
        return self._log_entry(log)

    
    def create_message(self, **kwargs):
        """
        Create a Message

        This instantiates an object with some convienent methods for handling
        a stream of text that will eventually be written to the Elog
        
        Returns
        -------
        :class:`.Message`
            Returns a Message object with the client as the parent
        """
        return Message(parent=self, **kwargs)

  
    def save_config(self, filename=None, heading='DEFAULT'):
        """
        Save the current client configuration to a file so that it can be
        quickly loaded again in a future session. This preserves logbooks,
        tags, username and url.

        Parameters
        ----------
        filename : string, optional
            The path to save the new configuration file. By default, a hidden
            file .pyElog.conf will be created in the user's home directory 

        heading : string, optional
            Optional choice to put a unique heading on the configuration. If
            switched to None, the current heading of the loaded configuration
            will be used
        """
        self._conf.save(filename = filename,
                        heading  = heading, 
                        tags     = self.active_tags,
                        logbooks = self.active_logbooks,
                        username = self._auth[0],
                        url      = self._url)


    def _logbook_service(self, logbook):
        """
        Return a LogBookWebService instance for a given Logbook
        """
        try:
            session = LogBookWebService(ins = logbook.area,
                                        sta = '',
                                        exp = logbook.name,
                                        usr = self._auth[0],
                                        url = self._url,
                                        pas = self._auth[1])
            return session

        except JSONDecodeError: #Nice if this was handled in LogBookWebService
            raise EnvironmentError('Unable to open session, check credentials')

    def _list_experiments(self, logbook):
        """
        Return a list of experiments for the area
        """
        session = self._logbook_service(logbook)
        return session.get_list_of_experiments()


    def _log_entry(self, entry):
        """
        Post a LogEntry object to the Elog
        """
        def log_post(logbook,logentry):
            session = self._logbook_service(logbook)
            info    = dict(logentry)

            #Load attachments
            if 'attachments' in info:
                info['files'],info['desc'] = [],[]

                for attach in info['attachments']:
                    info['files'].append(attach.filename)
                    info['desc'].append(attach.description)
            
            #Post to LBWS
            session.post_lists(msg      = info.get('text',''),
                               run      = info.get('run',''),
                               lst_tag  = info.get('tags', ['']),
                               lst_des  = info.get('desc', ['']), 
                               lst_att  = info.get('files',['']), 
                              ) 

        #Add entry to all specified logbooks 
        for book in entry.logbooks:
    
            try:
                log_post(book,entry)

            except KeyError as e:
                print e
                print 'No logbook "{}" exists in '\
                      'experimental area {}'.format(book.name, book.area)
                print 'Available logbooks are: '
                print self._list_experiments(book)
                
     
        
        return dict(entry) 

                                         
class Message(object):
    """
    A Class to represent a stream of text
    
    Parameters
    ----------
    parent : :class:`ElogClient` , optional
        Parent ElogClient to ulimately post the message

    kwargs : dictionary, optional
        Saved group of tags and/or attachments to be posted with message
        
    Attributes
    ----------
    parent : :class:`ElogClient`
        Parent ElogClient
    
    msg_store : string
        Saved message
    """
    msg_store = ''

    def __init__(self,parent=None,**kwargs):
        self.parent = parent
        self._post  = kwargs


    def write(self, text, quiet=True):
        """
        Add text to the Message store
        
        Parameters
        ----------
        text : str
            Desired text to add
        
        quiet : bool, optional
            The choice to print the message, as well as log
        """
        self.msg_store += text
        self.msg_store += '\n'

        if not quiet:
            print(text)        
       
 
    def edit(self):
        """
        Edit the existing message

        This opens the message store in a text editor allowing the option to
        retroactivaley edit previously entered messages.
        """
        self.msg_store = get_text_from_editor(postpend=self.msg_store)


    def post(self, clear=True, edit=False):
        """
        Post the message to the parent client
        
        
        Parameters
        ----------
        edit : bool, optional
            Edit the stored message before posting

        clear : bool, optional
            Clear the cached message

        Raises
        ------
        AttributeError
            If the parent object is not properly set
        """
        if not self.parent:
            raise AttributeError('No parent ElogClient for the Message')
 
        if edit: 
            self.edit()
        
        if not self.msg_store:
            return 

        post = self.parent.post(self.msg_store, **self._post)
        
        if clear:
            self.clear()

        return post


    def clear(self):
        """
        Clear the cached message
        """
        self.msg_store = ''


    def __str__(self):
        return self.msg_store

    def __repr__(self):
        lines = self.msg_store.count('\n')
        return '< Message object, {} lines >'.format(lines)
