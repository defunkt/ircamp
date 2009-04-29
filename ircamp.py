# sys
import re
from htmlentitydefs import name2codepoint as n2cp
from datetime import datetime

# twisted
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log

# pinder
import pinder

# BeautifulSoup
from BeautifulSoup import BeautifulSoup

# config
from settings import *

class CampfireBot(object):
    """The Campfire part of the IRC <-> Campfire bridge."""

    def __init__(self, subdomain, room, email, password):
        self.host = "http://%s.campfirenow.com" % subdomain
        self.subdomain = subdomain
        self.email = email
        self.client = pinder.Campfire(subdomain)
        self.client.login(email, password)
        self.room = self.client.find_room_by_name(room)
        self.room.join()

    def __str__(self):
        return "<%s: %s as %s>" % (self.host, self.room, self.email)

    def __getattr__(self, name):
        return getattr(self.room, name)

    def logout(self):
        self.room.leave()
        self.client.logout()

    def todays_transcript_url(self):
        path = '/room/%s/transcript/%s' % (self.id,
                                           datetime.now().strftime('%Y/%m/%d'))
        return self.host + path


# message filters

class MessageFilter(object):
    def __init__(self, message):
        self.message = message

    @classmethod
    def filter_message(cls, message):
        for subclass in cls.__subclasses__():
            message = subclass(message).filter()
        return message

    def filter(self):
        return self.message


class IRCMessageFilter(MessageFilter):
    pass


class TwitterFilter(IRCMessageFilter):
    def filter(self):
        if 'twitter.com/' in self.message:
            id = re.search(r'(\d+)', self.message).group(0)
            self.message = 'http://twictur.es/i/%s.gif' % id
        return self.message


class CampfireMessageFilter(MessageFilter):
    def __init__(self, message):
        self.message = message
        self.soup = BeautifulSoup(message['message'].decode('unicode_escape'))


class ActionFilter(CampfireMessageFilter):
    def filter(self):
        if re.search(r'has (entered|left) the room', self.message['message']):
            pass
        elif re.search(r'^\*(.+)\*$', self.message['message']):
            self.message['message'] = self.message['message'].replace('*', '')
        else:
            self.message['person'] = self.message['person'] + ':'

        return self.message


class PasteFilter(CampfireMessageFilter):
    def filter(self):
        paste = self.soup.find('pre')
        if paste:
            url = self.soup.find('a')['href']
            # hax
            host = "http://%s.campfirenow.com" % CAMPFIRE_SUBDOMAIN
            self.message['message'] = host + url
        return self.message


class ImageFilter(CampfireMessageFilter):
    def filter(self):
        image = self.soup.find('img')

        if image:
            url = str(image['src'])
            if "twictur.es" in url:
                url = self.twicture_url(url)
            self.message['message'] = url

        return self.message

    def twicture_url(self, image):
        return image.replace('/i/', '/r/').replace('.gif', '')


class LinkFilter(CampfireMessageFilter):
    def filter(self):
        link = self.soup.find('a')
        if link and len(self.soup.findAll(True)) == 1:
            self.message['message'] = str(link['href'])
        return self.message


class IRCBot(irc.IRCClient):
    """The IRC part of the IRC <-> Campfire bridge."""

    nickname = BOT_NAME

    # twisted callbacks

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.campfire = CampfireBot(self.factory.subdomain, self.factory.room,
                                    self.factory.email, self.factory.password)
        self.channel = '#%s' % self.factory.channel
        self.lc = task.LoopingCall(self.new_messages_from_campfire)
        self.lc.start(5, False)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.campfire.logout()

    def new_messages_from_campfire(self):
        self.campfire.ping()
        try:
            for message in self.campfire.messages():
                message = CampfireMessageFilter.filter_message(message)
                msg = "%s %s" % (message['person'], message['message'])
                msg = self.decode_htmlentities(msg.decode('unicode_escape'))
                self.speak(msg)
        except socket.timeout:
            pass

    # irc callbacks

    def signedOn(self):
        self.join(self.channel)
        self.commands = IRCCommands(campfire=self.campfire, irc=self)

    def joined(self, channel):
        self.speak("Room '%s' in %s: %s" %
                   (self.factory.room, self.factory.subdomain,
                    self.campfire.todays_transcript_url()))

    def irc_PING(self, prefix, params):
        irc.IRCClient.irc_PING(self, prefix, params)
        self.campfire.ping()

    def action(self, user, channel, data):
        user = user.split('!')[0]
        action = '*' + data + '*'

        if user == BLESSED_USER:
            self.campfire.speak(action)

        self.log(channel, user, action)


    def privmsg(self, user, channel, msg):
        user = user.split('!')[0]
        self.log(channel, user, msg)

        if user == BLESSED_USER:
            if self.iscommand(msg):
                parts = msg.split(' ')
                command = parts[1]
                args = parts[2:]
                out = self.commands._send(command, args)
                self.speak(out)
            else:
                out = IRCMessageFilter.filter_message(msg)
                self.campfire.speak(out)

    def iscommand(self, msg):
        return BOT_NAME in msg.split(' ')[0]

    # other bot methods

    def speak(self, message):
        self.msg(self.channel, str(message))
        self.log(self.channel, self.nickname, message)

    def log(self, channel, user, msg):
        print "%s <%s> %s" % (channel, user, msg)

    def __str__(self):
        return "<%s: %s as %s>" % (IRC_SERVER, self.channel, self.nickname)

    def decode_htmlentities(self, string):
        """
        Decode HTML entities-hex, decimal, or named-in a string
        @see http://snippets.dzone.com/posts/show/4569
        @see http://github.com/sku/python-twitter-ircbot/blob/321d94e0e40d0acc92f5bf57d126b57369da70de/html_decode.py
        """
        def substitute_entity(match):
            ent = match.group(3)
            if match.group(1) == "#":
                # decoding by number
                if match.group(2) == '':
                    # number is in decimal
                    return unichr(int(ent))
                elif match.group(2) == 'x':
                    # number is in hex
                    return unichr(int('0x'+ent, 16))
            else:
                # they were using a name
                cp = n2cp.get(ent)
                if cp: return unichr(cp)
                else: return match.group()

        entity_re = re.compile(r'&(#?)(x?)(\w+);')
        return entity_re.subn(substitute_entity, string)[0]


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

class IRCCommands(object):
    """
    Commands the IRC bot responds to.

    Each method is a command, passed all subsequent words.

    e.g.

    <defunkt> bot: help
    calls: bot.help([])

    <defunkt> bot: guest on
    calls: bot.guest(['on'])

    Returning a non-empty string replies to the channel.
    """
    def __init__(self, campfire, irc):
        self.campfire = campfire
        self.irc = irc

    def _send(self, command, args):
        """Dispatch method. Not a command."""
        try:
            method = getattr(self, command)
            return method(args)
        except:
            return ''

    def help(self, args):
        methods = dir(self)
        methods.remove('_send')
        methods = [x for x in methods if not '__' in x and type(getattr(self, x)) == type(self._send)]
        return "I know these commands: " + ', '.join(methods)

    def users(self, args):
        return ', '.join(self.campfire.users())


if __name__ == '__main__':
    f = IRCBotFactory()
    reactor.connectTCP(IRC_SERVER, IRC_PORT, f)
    reactor.run()
