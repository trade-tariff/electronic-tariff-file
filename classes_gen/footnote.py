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
        self.footnote_type_id = ""
        self.footnote_id = ""

    def format_text(self):
        self.FOOTNOTE_TEXT = f.format_string(self.FOOTNOTE_TEXT).strip()
        self.FOOTNOTE_LENGTH = str(len(self.FOOTNOTE_TEXT)).zfill(4)
        self.create_extract_line()
        
    def get_footnote_number(self):
        if self.footnote_type_id == "NC": # add 800
            self.FOOTNOTE_NUMBER = str(int(self.footnote_id) + 800)
        elif self.footnote_type_id == "PN": # add 900
            self.FOOTNOTE_NUMBER = str(int(self.footnote_id) + 900)
        else:
            self.FOOTNOTE_NUMBER = self.footnote_id

    def create_extract_line(self):
        self.extract_line = self.RECORD_TYPE + CommonString.divider
        self.extract_line += self.FOOTNOTE_NUMBER + CommonString.divider
        self.extract_line += self.FOOTNOTE_EDATE + CommonString.divider
        self.extract_line += self.FOOTNOTE_ETIME + CommonString.divider
        self.extract_line += self.FOOTNOTE_LDATE + CommonString.divider
        self.extract_line += self.FOOTNOTE_LTIME + CommonString.divider
        self.extract_line += self.FOOTNOTE_LENGTH + CommonString.divider
        self.extract_line += self.FOOTNOTE_TEXT
        self.extract_line += CommonString.line_feed
