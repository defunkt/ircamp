IRCamp: IRC <-> Campfire Bridge
===============================

IRCamp allows you to use Campfire from the comfort of your favorite IRC 
client by acting as a thin bridge between the two services.

It's currently a work in progress. I'm pretty sure it can't stay 
connected to Campfire very long. Working on this.

Requirements
------------

* Python 2.3+
* Pinder >= 0.6.5a (defunkt's fork)
* BeautifulSoup >= 3.0.4
* httplib2 >= 0.3.0
* Twisted >= 2.5.0


Installation
------------

    $ easy_install -U BeautifulSoup
    $ easy_install -U httplib2
    $ git clone git://github.com/defunkt/pinder.git
    $ cd pinder && python setup.py install
    $ git clone git://github.com/defunkt/ircamp.git    
    $ cd ircamp
    

Configuration
-------------

You'll want to create a local_settings.py inside your new `ircamp` 
directory. It should look something like this:

    BLESSED_USER       = "your_name"
    IRC_CHANNEL        = "private_room"
    CAMPFIRE_SUBDOMAIN = "mycompany"
    CAMPFIRE_ROOM      = "The Good Room"
    CAMPFIRE_EMAIL     = "ircamp@gmail.com"
    CAMPFIRE_PASSWORD  = "1rc4mp"

The bot will only respond to `BLESSED_USER`, so ensure it's a registered
irc nickname.


Usage
-----

    $ python ircamp.py


Bugs! Features!
---------------

Please add them to http://github.com/defunkt/ircamp/issues

Thanks.

Chris Wanstrath // chris@ozmm.org
