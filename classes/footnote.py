class Footnote(object):
    def __init__(self, line=""):
        if line != "":
            self.line = line
            self.parse()

    def parse(self):
        self.RECORD_TYPE = self.line[0:2]
        self.FOOTNOTE_NUMBER = self.line[2:5]
        self.FOOTNOTE_EDATE = self.line[5:13]
        self.FOOTNOTE_ETIME = self.line[13:19]
        self.FOOTNOTE_LDATE = self.line[19:27]
        self.FOOTNOTE_LTIME = self.line[27:33]
        self.FOOTNOTE_LENGTH = self.line[33:37]
        self.FOOTNOTE_TEXT = self.line[37:].rstrip()
        self.line = ""
