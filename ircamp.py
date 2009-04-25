# twisted
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log

# pinder
import pinder

# config
from settings import *

class CampfireBot(object):
    """The Campfire part of the IRC <-> Campfire bridge."""

    def __init__(self, subdomain, room, email, password):
        self.client = pinder.Campfire(subdomain)
        self.client.login(email, password)
        self.room = self.client.find_room_by_name(room)

    def logout(self):
        self.room.leave()
        self.client.logout()

    def __getattr__(self, name):
        return getattr(self.room, name)

class IRCBot(irc.IRCClient):
    """The IRC part of the IRC <-> Campfire bridge."""

    nickname = "ircamp"

    # twisted callbacks

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.campfire = CampfireBot(self.factory.subdomain, self.factory.room, self.factory.email, self.factory.password)
        self.channel = '#%s' % self.factory.channel
        self.lc = task.LoopingCall(self.new_messages_from_campfire)
        self.lc.start(5, False)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.campfire.logout()

    def new_messages_from_campfire(self):
        self.campfire.ping()
        for message in self.campfire.messages():
            self.msg(self.channel, "%s: %s" % (message['person'], message['message']))

    # irc callbacks

    def signedOn(self):
        self.join(self.channel)

    def joined(self, channel):
        self.msg(channel, "I'm room '%s' in the %s campfire." % (self.factory.room, self.factory.subdomain))

    def irc_PING(self, prefix, params):
        irc.IRCClient.irc_PING(self, prefix, params)
        self.campfire.ping()

    def privmsg(self, user, channel, msg):
        user = user.split('!')[0]

        if user == BLESSED_USER:
            self.campfire.speak(msg)

        print "%s <%s> %s" % (channel, user, msg)

class IRCBotFactory(protocol.ClientFactory):
    """
    A factory for IRCBot.

    A new protocol instance will be created each time we connect to the server.
    """

    protocol = IRCBot

    def __init__(self):
        self.channel = IRC_CHANNEL
        self.subdomain = CAMPFIRE_SUBDOMAIN
        self.room = CAMPFIRE_ROOM
        self.email = CAMPFIRE_EMAIL
        self.password = CAMPFIRE_PASSWORD

    def clientConnectionLost(self, connector, reason):
        """Reconnect to server on disconnect."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    f = IRCBotFactory()
    reactor.connectTCP(IRC_SERVER, IRC_PORT, f)
    reactor.run()
