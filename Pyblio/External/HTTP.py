import os
import struct
import socket
from twisted.web import client
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.names.client import getHostByName
from twisted.python import log

# provide SOCKS access if needed
socks = os.getenv('SOCKS')
if socks:
    socks_addr, socks_port = socks.split(':')
    socks_port = int(socks_port)

class SOCKS4Protocol(Protocol):
    """Implementation of subset of SOCKS4.

    Once the communication is established, this class behaves as a
    transport for the client that instanciated it.
    """
    def connectionMade(self):
        self.established = False
        self.buf = ""
        log.msg("SOCKS connection to %s" % self.factory.addr)
        data = struct.pack('!BBH', 0x04, 0x01, self.factory.port)
        data += socket.inet_aton(self.factory.addr)
        data += 'pyblio\0'
        self.transport.write(data)

    def dataReceived(self, data):
        if not self.established:
            self.buf += data
            if self.buf < 8:
                return
            try:
                _, status, port = struct.unpack('!BBH', self.buf[:4])
            except struct.error:
                raise RuntimeError("invalid reply")
            addr = socket.inet_ntoa(self.buf[4:])
            if status == 0x5a:
                self.established = True
                # these are here to make this behave as a transport
                self.disconnecting = False
                # the client will use self as its transport
                self.p = self.factory.client.buildProtocol(addr)
                self.p.transport = self
                self.p.connectionMade()
            else:
                raise RuntimeError("SOCKS connection refused: %x" % status)

            if self.buf > 8:
                self.p.dataReceived(self.buf[8:])
            return
        self.p.dataReceived(data)

    def connectionLost(self, reason):
        log.msg("SOCKS connection lost: %s" % reason)
        self.p.connectionLost(reason)

    def write(self, data):
        assert self.established
        self.transport.write(data)

    def loseConnection(self):
        self.transport.loseConnection()

class SOCKS4Client(ClientFactory):
    """ A SOCKS4 connection to a server."""
    protocol = SOCKS4Protocol

    def __init__(self, addr, port, client):
        self.addr = addr
        self.port = port
        self.client = client

    def clientConnectionFailed(self, connector, reason):
        self.client.clientConnectionFailed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        self.client.clientConnectionLost(connector, reason)

class HTTPRetrieve(client.HTTPClientFactory):
    """ Cancellable HTTP client.
    
    This HTTP getter keeps track of the running protocol
    instances, so that their transport can be closed in the middle of
    an operation."""
    
    def __init__(self, url, *args, **kargs):
        client.HTTPClientFactory.__init__(self, url, *args, **kargs)

        self.running = []

        scheme, host, port, path = client._parse(url)
        if socks:
            def connectToIP(ip):
                self.socks = SOCKS4Client(ip, port, self)
                reactor.connectTCP(socks_addr, socks_port, self.socks)
            def failed(failure):
                self.deferred.errback(failure)
            getHostByName(host).addCallback(connectToIP).addErrback(failed)
        else:
            reactor.connectTCP(host, port, self)
        return
    
    def buildProtocol(self, addr):
        p = client.HTTPClientFactory.buildProtocol(self, addr)
        self.running.append(p)
        return p

    def cancel(self):
        self.running[-1].transport.loseConnection()
        return

