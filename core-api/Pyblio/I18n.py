class Localize (object):

    def __init__ (self):
        import locale

        lang, charset = locale.getlocale (locale.LC_MESSAGES)

        self.lang = lang or ''
        self.lang_one = self.lang.split ('_') [0]

        return

    def trn (self, table):

        if table.has_key (self.lang):
            return table [self.lang]
        
        if table.has_key (self.lang_one):
            return table [self.lang_one]

        return table ['']
