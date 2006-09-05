# -*- python -*-

from twisted.application import internet, service
from nevow import appserver

from pubmed import Page

application = service.Application("pubmed")

site = appserver.NevowSite(Page())

server = internet.TCPServer(1234, site)
server.setServiceParent(application)
