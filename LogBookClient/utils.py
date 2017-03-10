import os
import tempfile
import subprocess

from .datatypes import Attachment

text_message = '''
#
# Please enter the log message using the editor. Lines beginning with '#' will
# be ignored, and an empty message aborts the log message from being logged.
#
'''


def get_screenshot(root=False,itype='png',description=None):
    """
    Open ImageMagick and get screengrab
    
    Parameters
    ----------
    root : bool, optional
        If True, the entire screen is automatically selected. Otherwise, a
        smaller portion can be grabbed 

    itype: string, optional
        Choice of image file type

    description: string, optional
        Short description of screenshot

    Returns
    -------
    String of entered text
    """
    if root:
        opts = '-window-root'
    
    else:
        opts = ''

    image = subprocess.Popen('import {0} {1}:-'.format(opts,itype),
                             shell=True,
                             stdout=subprocess.PIPE)

    img = image.communicate()[0]
    tmp = tempfile.NamedTemporaryFile(mode='r+b', suffix='.'+itype, delete=False)
    tmp.file.write(img) 
    
    return Attachment(tmp.name, desc=description)


def get_text_from_editor(prepend=None,postpend=None):
    """
    Open a text editor and return the text
    
    Parameters
    ----------
    prepend : string, optional
        Optional prompt to put in at the beginning of the editor

    postpend : string, optional
        Optional prompt to display after the default message prompt  
    
    Returns
    -------
        Attachment object with text from the editor 
    """
    with tempfile.NamedTemporaryFile(suffix='.tmp',mode='w+t') as f:
        
        message = ''
        
        if prepend:
            message += '\n\n'
            message += prepend
            message += '\n'


        message += text_message


        if postpend:
            message += postpend

        f.write(message)
        f.flush()


        editor = os.environ.get('EDITOR', 'vim')
        subprocess.call([editor, f.name])


        #Read file back
        f.seek(0)
        text = f.read()

        #Strip off any lines that start with whitespace and a '#'
        lines = [n for n in text.splitlines()
                 if not n.lstrip().startswith('#')]
        text  = '\n'.join(lines) 

    return text


def save_pyplot_figure(**kwargs):
    """
    Save a matplotlib figure to an Elog Attachment
    
    All optional keywords are passed to the `savefig` matplotlib function
    
    Returns
    -------
    A list of Attachment objects, one pdf of the graph, and one thumbnail
    """
    import matplotlib.pyplot as plt
    import StringIO

    imgdata = StringIO.StringIO()
    plt.savefig(imgdata,format='pdf',**kwargs)
    imgdata.seek(0)

    a = [Attachment(imgdata,'plot.pdf')]
    
    imgdata = StringIO.StringIO()
    plt.savefig(imgdata, format='png', dpi=50,
                **kwargs)

    imgdata.seek(0)

    a.append(Attachment(imgdata,'thumbnail.png'))

    return a

