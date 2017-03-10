from __future__ import print_function

import os
import six
import json
import string
import mimetypes

class LogEntry(object):
    """
    A LogEntry consists of some text description, an author and a group of
    associated logbooks. It also contains associated tags and attachments
        
    Parameters
    ---------
    text: string, optional
        Text of Log Entry

    author: string
        Author of LogEntry

    logbooks: LogBook, or list of Logbook objects
        Logbooks to add LogEntry

    tags: string, list of strings, Tag object, optional
        Appropriate tags to associate with the LogEntry

    attachments: Attachment or list of Attachment objects, optional
        Attachments for Entry

    run : string
        Run number for post
    """

    def __init__(self, text=None, author=None, logbooks=None,
                 tags=None, attachments=None, run=None):
        #Make sure all characters are printable
        if text is not None:
            text = ''.join(c for c in text if c in string.printable)
        else:
            text = ''

        
        self.text   = text.strip()
        self.tags   = tags
        
        if author is None:
            raise ValueError('You must specify an author')
        else:
            self.author = author
        
        if logbooks is None:
            raise ValueError('You must specify a logbook')
        else:
            self.logbooks = logbooks
        
        if attachments is not None:
            self.attachments = attachments
        else:
            self.attachments = []

        if tags is not None:
            self.tags = tags
        else:
            self.tags = []

        if run:
            self.run = '{}'.format(run).strip()
        else:
            self.run = ''
            
 
    def __iter__(self):
        rtn = list()
        
        def update(name,value):
            if value:
                try:
                    iter(value)
                
                except TypeError:
                    pass 

                else:
                    if name == 'tags':
                        if any(isinstance(x, Tag) for x in value):
                            value = [v.name for v in value]
                        
                        elif isinstance(value,six.string_types):
                            value = [value]
                     
                rtn.append((name,value))


        update('text',         self.text)
        update('author',       self.author)
        update('logbooks',     self.logbooks)
        update('tags',         self.tags)
        update('run',          self.run)
        update('attachments',  self.attachments)
        return iter(rtn)


class Tag(object):
    """
    A Tag consists of a unique name, used to identfy entries
    
    Parameters
    ----------
    name : string
        Name of tag

    active : bool
        Choice to have tag be active

    Example
    -------
    >>> Tag('Laser Timing')
    """
    def __init__(self,name, active = True):
        self.name = '{}'.format(name).strip() #Allow some type flexibility

        if active:
            self.state = 'Active'
        else:
            self.state = 'Inactive'


    @property
    def active(self):
        """
        A property to active / deactivate the Tag
        """
        if self.state == 'Active':
            return True
        else:
            return False


    @active.setter
    def active(self,value):
        if value:
            self.state == 'Active'
        else:
            self.state = 'Inactive'
    

    def __cmp__(self,*arg, **kwargs):
        if arg[0] is None:
            return 1
        return cmp(self.name, arg[0].name)
    
    def __repr__(self):
        return '<Tag Object :{}, State :{}>'.format(self.name,
                                                    self.state) 

class Attachment(object):
    """
    A class representation of an ELog Attachment.
        
    Parameters
    ----------
    filename: string 
        Filename of attachment

    desc : string, optional
        A short description of the attached file

    Example
    -------
    >>> Attachment(filename='home/myplot.plt')
    """

    def __init__(self, filename , desc=''):
        self.filename    = filename
        self.description = '{}'.format(desc).strip()
   
 
    def get_file_post(self):
        """
        Return tuple of file postings
        """
        basename = os.path.basename(self.filename)
        
        return (basename, self.file, self.description)

    
    def __repr__(self):
        return '<Attachment from file {}>'.format(self.filename)


class Logbook(object):
    """
    Class to represent a Logbook

    Elog pages are identified by two major pieces of information, an area and
    name. These are usually represented in text at the top of the HTML page as
    `{area} / {name}`. Keep in mind that the combination of area and name might
    not be intuitiive. For instance, all of the facilities Logbooks are
    classified as being in the NEH area, with each logbook identified as
    `{hutch} Instrument.`  
   
    Parameters
    ----------
    area : string
        The three letter acronym for the Experimental Area, capitalization
        optional. 

    name : string, optional
        Name of the Elog requested. By default, the current experiment for the
        area will be used. For the facilities logbooks, there is not concept of
        a current experiment so this should be entered

    active : bool, optional
        Initialize the logbook as active or not
    """
    def __init__(self, area=None, name=None, 
                 active=True):
        
        self.area  = area.upper().strip()
        
        if not name:
            self.name = 'current' 
        else:
            self.name = name.strip()
        
        if active:
            self.state = 'Active'
        
        else:
            self.state = 'Inactive'


    @property
    def active(self):
        """
        A property to active / deactivate the Tag
        """
        if self.state == 'Active':
            return True
        else:
            return False


    @active.setter
    def active(self,value):
        if value:
            self.state == 'Active'
        else:
            self.state = 'Inactive'

    
    def __cmp__(self,*arg,**kwargs):
        if arg[0] is None:
            return 1
        
        return cmp((self.area,   self.name),
                   (arg[0].area, arg[0].name))

 
    def __repr__(self):
        return '<Logbook for {} in {}, status: {}>'.format(self.name,
                                                           self.area,
                                                           self.state,)



