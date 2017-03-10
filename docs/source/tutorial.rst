Tutorial
********
The Elog module contains the same basic functionality of older renditions, a
single client to post messages to the log. However, for higher level
applications that want to intelligently post more complex information i.e
streaming text, screenshots, e.t.c, this API provides a number of useful
methods. A lot of groups have independently created solutions for a few of
these problems, but the goal of this version was to combine these into a
central location. 

Basic Setup
^^^^^^^^^^^
The Elog mBasic Setupodule uses one central object, :class:`.ElogClient` to hold
connections to any number of logbooks and tags. An example of the most basic
configuration can be seen below.    

.. code-block:: python

    from LogBookClient import ElogClient
    
    elog = ElogClient(username='mfxopr')
    elog.add_logbook('mfx')  #This adds the current experimental Elog

    elog.post('Text I want placed in the Elog')

In previous modes, specifying which logbook you wanted was slightly awkward. In
this rendition, this should be simplified. Each Logbook has an area and name
associated with it. The assumption was made that 99% of applications would only
need either an experimental Elog or the facilities Elog for an experimental
hutch, so the method :meth:`.ElogClient.add_logbook` wraps these convienently
with a couple keywords.

.. code-block:: python

    elog.add_logbook('mfx')                        #Current experimental Elog
    elog.add_logbook('mfx',facilities=True)        #Instrument Elog
    elog.add_logbook('mfx',experiment='mfxa1234')  #Past experiment logbook

If you need to add a Logbook that doesn't fall into these categories see the
documentation on instantiating a :class:`.Logbook` by itself, and append it to
the list found at :attr:`.ElogClient.logbooks`.

Managing Logbooks and Tags
^^^^^^^^^^^^^^^^^^^^^^^^^^
You may have noticed that the new client allows for multiple Logbooks to be
managed by a single client. However, you might not want every post to go to
each logbook. Using both the `active` keyword in
:meth:`.ElogClient.add_logbook` and the :meth:`.ElogClient.activate_logbook` method,
switching between loaded logbooks should be easy. 

The same system is used for managing tags. While looking at a number of the use
cases of the older Elog clients, it seemed that many modules had a specific tag
they wanted on every post. This meant a lot of extra typing to make sure that
every call to post had the right collection of tags. This should be much
simpler in the newer version. The same basic set of methods as described for
the logbooks are available for tags.

.. code-block:: python

    #Create Tags
    elog.create_tag('First Tag')
    elog.create_tag('Second Tag', active=False)

    elog.post("Start of the tutorial") #Only 'First Tag' will be added

    #Switch active tags
    elog.activate_tag('Second Tag',active=True)
    elog.activate_tag('First Tag',active=False)

    elog.post("Second step") #Only 'Second Tag' will be added
 
However, unlike the logbook, tags can be added to your post without being
instantiated first, using the ``tags`` keyword. This ignores the active set of
tags and posts the single tag, or list of tags given to
:meth:`.ElogClient.post`.

Messages
^^^^^^^^
As mentioned in the overview, one of the goals of this rendition of the
ElogClient is to accomodate more complex use cases than single message posts.
Instead, if we want the post to represent the output of a program or the steps
of a long a process, a stream of text must be captured. It is probably not
desirable in these situations to make a single post to the Elog for each
individual message, we would rather have a single post that captures the output
and posts it as a single message with the correct tags. The :class:`.Message`
object allows you to instantiate a file-like object that can be written,
viewed, and edited. 

First instantiate the message from the client

.. code-block:: python

    msg = elog.create_message()

Then you can begin writing to the message object as if it were a file

.. code-block:: python

    msg.write('Step 1 complete')
    msg.write('Complication in Step 2')

Finally, once your are satisfied you can view and edit the text, using
:meth:`.Message.edit` and post the message to the Elog by calling
:meth:`.Message.post`. Keep in mind that the tags and logbooks used to post the
message will be the ones active in the :attr:`.Message.parent` client. That
means that if you create the `Message` object, then change the tags and
logbooks before posting, the Elog will reflect the changes. If this
behavior is undesirable, you can pass tags and attachments as keywords into
:meth:`.ElogClient.create_message`, and only they will be reflected in the final
posting.

.. _configs:

Keeping Configurations
^^^^^^^^^^^^^^^^^^^^^^
One of the major downsides of the previous client, was it was difficult to
create code to post in the Elog that was agnostic of which hutch you were in.
This module addresses this by having user specific configurations saved to
files, where you can provide a username, password, list of tags, and list of
logbooks that you want to automatically be loaded by the client. This means in
any application you can just instantiate a logbook client, post messages, and
the user's configuration will determine where this is posted.

The underlying loading and saving of configurations relies on the
``configparser`` module in the Python stdlib. This creates a clean and human
readable file to store parameters within. Upon initialization, if no file was
passed using the ``config`` keyword when starting up :class:`.ElogClient`, a
few files are requested around the users home directory; ~/pyElog.conf,
~/.pyElog.conf, ~/.pyElog.rc, and pyElog.conf. If the client does not find any
configuration file, the current username will be used, a password requested,
and all logbooks and tags will have to be manually added. 

While these configurations can be written by hand, the client has a
convienent way to create these files using the
:meth:`.ElogClient.save_config`. Simply create a client instance, load the tags
and logbooks you need and save the configuration to a file of your choosing.

Here is an example of how we could create one for the mfxopr account

.. code-block:: python
 
    elog = ElogClient('mfxopr')
    
    #Add both hutch and current experimental Logbooks
    elog.add_logbook('mfx',facilities = True)
    elog.add_logbook('mfx')

    #Create a Tag to indicate the message source
    elog.create_tag('pyElog')
   
    #Save the configuration to a file of your choosing 
    elog.save_config('pyeElog.conf')


Now, whenever you want this configuration to be used, simply pass the file to
the client at initialization. If you want it to be automatically found, simply
place in in of the locations listed above. The configuration does have the
potential to save passwords for users. However, this is not done automatically
by the client, instead, these need to be entered by hand. Please if you choose
to do this, put the proper protections in place so that this file is only
visible to you. 

The goal of this is to not only have configurations for individual uses, but
also to possibly have configurations in place for specific modules. This way
more Python applications could share information to the Elog without creating
too much of a hassle for the author.


.. _interactive:
 
Interactive Use
^^^^^^^^^^^^^^^
By creating a streamlined API to load the eLog client, we can begin creating
tools to easily embed eLog capabilities into commonly used modules. Since a
majority of the Python tools developed at LCLS are used in an IPython
environment, this made an obvious starting point to display some of the
capabilities of the new client.

The LogBookClient module takes advantage of the IPython magics class to quickly
load classes and functions into your session. For optimal usage it is helpful
to have your configuration defined as suggested in the :ref:`configs` section.
Using the IPython magic method ``load_ext``, load the elog extension contained
within the module. This should search for saved configurations and instantiate
an :class:`ElogClient` instance under the alias ``elog`` with the pre-defined
logbooks and tags. For instance, using the configuration we defined above, the
following tags and logbooks should be loaded.

.. code-block:: python

    #Load the IPython eLog extension
    >>> %load_ext LogBookClient.ipy_extension
    >>> elog
    <LogBookClient.client.ElogClient at 0x2ba321bb5450> 
    >>> elog.active_logbooks
    [<Logbook for current in MFX, status: Active>,
     <Logbook for MFX Instrument in NEH, status: Active>]
    >>> elog.active_tags
    ['pyElog']

 
Now that we have checked that we have the correct configuration, we can begin
using some of the newly created magic functions. For instance, for a rapid post
to Logbook can be done using :meth:`.log_it`.

.. code-block:: python
    
    %log_it This is the messsage I want to post

In addition, the IPython terminal gives us the capability to record printed
output, allowing us to essentially record parts of our session. Here we
instantiate a dummy function to print to the console, and record a call. 

.. code-block:: python

    def func_with_print(num):
        for i in range(num):
            print 'Counting towards {}, currently at {}'.format(num, i)

    >>> %log_add func_with_print(5)
    Counting towards 5, currently at 0
    Counting towards 5, currently at 1
    Counting towards 5, currently at 2
    Counting towards 5, currently at 3
    Counting towards 5, currently at 4
    

This output will be stored but not automatically posted, allowing us to string
together a chain of function calls if we choose. Finally, to post the message,
we simple use :meth:`.log_end`. This will open an editor with the choice of
adding a note, or annotation to accompany the saved output. There is also the
:meth:`.grab_it` method that allows you to quickly take a screenshot. 
