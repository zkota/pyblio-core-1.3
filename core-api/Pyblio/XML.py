from xml import sax
from xml.sax.saxutils import escape


class Parser (sax.handler.ContentHandler):

    """ This class parses the XML format of a Schema """

    def setDocumentLocator (self, locator):
        self.locator = locator
        return
    
    def _error (self, msg):
        raise sax.SAXParseException (msg, None, self.locator)

    def _attr (self, attr, attrs):

        try:
            val = attrs [attr]
        except KeyError:
            self._error (_("missing '%s' attribute") % attr)

        return val
