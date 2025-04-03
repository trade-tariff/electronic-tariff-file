import csv
import os
import classes.globals as g


class FootnoteParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.footnotes = []
        file = open(g.parsed_file, "r")
        for line in file:
            if line[0:2] == "FN":
                ac = ParsedFootnote(line)
                self.footnotes.append(ac.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.parse_folder, "footnotes.csv")
        csv_columns = [
            "RECORD_TYPE",
            "FOOTNOTE_NUMBER",
            "FOOTNOTE_EDATE",
            "FOOTNOTE_ETIME",
            "FOOTNOTE_LDATE",
            "FOOTNOTE_LTIME",
            "FOOTNOTE_LENGTH",
            "FOOTNOTE_TEXT",
            "line",
        ]

        with open(csv_file, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for footnote in self.footnotes:
                writer.writerow(footnote)


class ParsedFootnote(object):
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
