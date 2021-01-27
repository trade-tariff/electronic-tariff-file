from classes.functions import functions as f
from classes.enums import CommonString

class Footnote(object):
    def __init__(self):
        self.RECORD_TYPE = "FN"
        self.FOOTNOTE_NUMBER = ""
        self.FOOTNOTE_EDATE = ""
        self.FOOTNOTE_ETIME = "000000"
        self.FOOTNOTE_LDATE = ""
        self.FOOTNOTE_LTIME = "000000"
        self.FOOTNOTE_LENGTH = None
        self.FOOTNOTE_TEXT = ""
        self.extract_line = None

    def format_text(self):
        self.FOOTNOTE_TEXT = f.format_string(self.FOOTNOTE_TEXT).strip()
        self.FOOTNOTE_LENGTH = str(len(self.FOOTNOTE_TEXT)).zfill(4)
        self.create_extract_line()

    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE
        self.extract_line += self.FOOTNOTE_NUMBER
        self.extract_line += self.FOOTNOTE_EDATE
        self.extract_line += self.FOOTNOTE_ETIME
        self.extract_line += self.FOOTNOTE_LDATE
        self.extract_line += self.FOOTNOTE_LTIME
        self.extract_line += self.FOOTNOTE_LENGTH
        self.extract_line += self.FOOTNOTE_TEXT
        self.extract_line += CommonString.line_feed
