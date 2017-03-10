from __future__ import print_function

from IPython.utils.io   import capture_output
from IPython.core.magic import Magics, magics_class, line_magic

from ..      import ElogClient
from ..utils import save_pyplot_figure, get_screenshot, get_text_from_editor

elog_client = ElogClient()

def post_elog(msg=None, edit=True, tags=None,
         attachments=None, **kwargs):
    """
    Submit a message to the current Elog client
    """
    if not msg: 
        msg = get_text_from_editor()
    
    if not msg:
        return

    return elog_client.post(msg, tags=tags,
                            attachments=attachments)



def elog_savefig(**kwargs):
    """
    Save a matplotlib figure and place it in the Elog
    
    The **kwargs are all passed onto to the function
    ``matplotlib.pyplot.savefig` and then onto the :func:`.post_elog` function
    """
    fig = save_pylot_figure(**kwargs)
    if 'attachments' in kwargs:
        if isinstance(kwargs['attachments'],list):
            kwargs['attachments'].append(fig)

        else:
            kwargs['attachments'] = [kwargs['attachments'], fig]

    else:
        kwargs['attachments'] = fig

    return post_elog(**kwargs)


def elog_grab(root=False, **kwargs):
    """
    Grab a screenshot and place it in the Elog
    
    Parameters
    ----------
    root: bool, optional
        If true, the entire screen is grabbed, else select rubberband
    """
    if not root:
        print('Select an area of the screen to grab ............')
    
    try:
        a = get_screenshot(root)

    except KeyboardInterrupt:
        print('Canceled, no entry created')
        return

    if 'attachments' in kwargs:
        if isinstance(kwargs['attachments'],list):
            kwargs['attachments'].append(a)

        else:
            kwargs['attachments'] = [kwargs['attachments'], a]

    else:
        kwargs['attachments'] = a

    return post_elog(**kwargs)
        


@magics_class
class ElogMagics(Magics):
    """
    The ElogMagics class contains a few special methods to help users quickly
    access the Elog in an IPython session.

    Example
    -------
    >>> %load_ext LogBookClient.cli.ipy
    >>> %log_it 'Important message'
    >>> %log_add func_with_print()

    """ 
    msg_store = ''

    @line_magic
    def log_add(self, line):
        """
        Run the line and capture the output for the Elog

        .. note::
 
            This function currently only captures output printed to the
            terminal. Therefore, if the method run returns a string it will not
            be included.
        """
        #Add a command to message store
        self.msg_store += ">>>{}\n".format(line)
        self.msg_store += '\n'
        
        #Run the command
        with capture_output() as c:
            self.shell.run_cell(line)
        c.show()
        
        #Save the output to the message store
        self.msg_store += c.stdout
        self.msg_store += '\n'


    @line_magic
    def log_end(self, line):
        """
        Publish the stored messages in the Elog
        """
        text = get_text_from_editor(prepend=self.msg_store)

        if not text:
            return

        post_elog(text)
        self.msg_store = ''


    @line_magic
    def log_clear(self, line):
        """
        Clear the stored lines
        """
        self.msg_store = ''
        

    @line_magic
    def log_it(self, line):
        """
        Add the line to the Elog
        """
        if line.rstrip() == '':
            post_elog()

        else:
            post_elog(line.strip())


    @line_magic
    def grab_it(self, line):
        """
        Grab a screenshot and add it to the Elog
        """
        elog_grab()


def load_ipython_extension(ipython):
    push_vars = {'elog'         : elog_client,
                 'elog_savefig' : elog_savefig,
                 'elog_grab'    : elog_grab,
                }
    ipython.push(push_vars)
    ipython.register_magics(ElogMagics) 

