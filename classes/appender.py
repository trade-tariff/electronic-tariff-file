import csv
import os
import sys
import classes.globals as g
from classes.measure import Measure
from classes.enums import CommonString


class Appender(object):
    def __init__(self):
        self.commodity = ""
        self.filename = os.path.join(g.app.data_in_folder, "hmce-tariff-ascii-jan2021.original.txt")
        self.csv_file = os.path.join(g.app.reference_folder, "pr.measures.txt")

    def parse(self):
        self.measures = []
        file = open(self.filename, "r")
        for line in file:
            if line[0:2] == "CM":
                self.commodity = line[2:12]
            elif line[0:4] == "MEPR":
                measure = Measure(line, self.commodity)
                self.measures.append(measure)

    def create_csv(self):
        with open(self.csv_file, 'w') as csvfile:
            for measure in self.measures:
                measure.line = measure.line.strip()
                line = '"' + measure.commodity + '","' + measure.line + '"' +  + CommonString.line_feed
                csvfile.write(line)
