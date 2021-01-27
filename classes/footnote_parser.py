import csv
import os
import sys
import classes.globals as g
from classes.footnote import Footnote


class FootnoteParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.footnotes = []
        self.filename = os.path.join(g.app.data_in_folder, "footnotes_only.txt")
        file = open(self.filename, "r")
        for line in file:
            footnote = Footnote(line)
            self.footnotes.append(footnote.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.app.data_out_folder, "footnotes.csv")
        csv_columns = [
            'RECORD_TYPE', 'FOOTNOTE_NUMBER', 'FOOTNOTE_EDATE', 'FOOTNOTE_ETIME',
            'FOOTNOTE_LDATE', 'FOOTNOTE_LTIME', 'FOOTNOTE_LENGTH', 'FOOTNOTE_TEXT', 'line']
        
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for footnote in self.footnotes:
                writer.writerow(footnote)
