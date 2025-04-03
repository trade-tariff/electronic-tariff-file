import csv
import os
import classes.globals as g


class AdditionalCodeParser(object):
    def __init__(self):
        pass

    def parse(self):
        self.additional_codes = []
        file = open(g.parsed_file, "r")
        for line in file:
            if line[0:2] == "CA":
                ac = ParsedAdditionalCode(line)
                self.additional_codes.append(ac.__dict__)

    def create_csv(self):
        csv_file = os.path.join(g.parse_folder, "additional_codes.csv")
        csv_columns = ["RECORD_TYPE", "EC_SUPP_COUNT", "CODE_STRING", "line"]

        with open(csv_file, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for additional_code in self.additional_codes:
                writer.writerow(additional_code)


class ParsedAdditionalCode(object):
    def __init__(self, line):
        self.line = line.strip()
        self.parse()

    def parse(self):
        self.RECORD_TYPE = self.line[0:2]
        self.EC_SUPP_COUNT = self.line[2:6]

        line_length = len(self.line)
        ac_length = line_length - 6
        ac_count = int(ac_length / 4)

        self.CODE_STRING = ""
        for i in range(0, ac_count):
            self.CODE_STRING += self.line[6 + (i * 4) : 6 + (i * 4) + 4] + ":"
        self.CODE_STRING = self.CODE_STRING.strip(":")

        self.line = ""
