# the bot only listens to one user.
BLESSED_USER = "your_name"

IRC_CHANNEL = "private_room"
IRC_SERVER  = "irc.freenode.net"
IRC_PORT    = 6667

CAMPFIRE_SUBDOMAIN = "mycompany"
CAMPFIRE_ROOM      = "The Good Room"
CAMPFIRE_EMAIL     = "ircamp@gmail.com"
CAMPFIRE_PASSWORD  = "1rc4mp"

try:
    from local_settings import *
except ImportError:
    pass
