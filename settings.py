# create a local_settings.py and overwrite
# these values:

BLESSED_USER       = "your_name"  # the bot only listens to one user.
IRC_CHANNEL        = "private_room"
CAMPFIRE_SUBDOMAIN = "mycompany"
CAMPFIRE_ROOM      = "The Good Room"
CAMPFIRE_EMAIL     = "ircamp@gmail.com"
CAMPFIRE_PASSWORD  = "1rc4mp"




# you probably don't want anything below
# this line in local_settings.py

IRC_SERVER  = "irc.freenode.net"
IRC_PORT    = 6667

try:
    from local_settings import *
except ImportError:
    pass
