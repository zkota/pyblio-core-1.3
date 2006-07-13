from twisted.web import client
from twisted.internet import reactor


class HTTPRetrieve(client.HTTPClientFactory):
    """ Cancellable HTTP client.
    
    This HTTP getter keeps track of the running protocol
    instances, so that their transport can be closed in the middle of
    an operation."""
    
    def __init__(self, url, *args, **kargs):
        client.HTTPClientFactory.__init__(self, url, *args, **kargs)

        self.running = []

        scheme, host, port, path = client._parse(url)
        reactor.connectTCP(host, port, self)
        return
    
    def buildProtocol(self, addr):
        p = client.HTTPClientFactory.buildProtocol(self, addr)
        self.running.append(p)
        return p

    def cancel(self):
        self.running[-1].transport.loseConnection()
        return

