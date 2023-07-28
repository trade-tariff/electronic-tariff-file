import os
import sys
import re

from classes.footnote_parser import FootnoteParser
from classes.additional_code_parser import AdditionalCodeParser
from classes.commodity_parser import CommodityParser
from classes.measure_parser import MeasureParser

import classes.globals as g


class Parser(object):
    def __init__(self):
        g.parse_folder = os.path.join(os.getcwd(), "parse")
        self.get_export_folder()
        os.makedirs(g.parse_folder, exist_ok=True)

    def get_export_folder(self):
        filename = None
        g.export_folder = os.path.join(os.getcwd(), "_export")
        subdirs = [x[0] for x in os.walk(g.export_folder)]
        subdirs.sort(reverse=True)
        for subdir in subdirs:
            if "icl_vme" in subdir:
                pattern = "[0-9]{4}-[0-9]{2}-[0-9]{2}"
                matches = re.search(pattern, subdir).regs
                if len(matches) > 0:
                    match = matches[0]
                    date_part = subdir[match[0]:match[1]]
                    filename = "hmrc-tariff-ascii-{date_part}.txt".format(date_part=date_part)
                    break

        if filename is None:
            print("No files found")
            sys.exit()
        else:
            g.parsed_file = os.path.join(subdir, filename)

    def parse(self):
        # Do the comm codes
        parser = CommodityParser()
        parser.parse()
        parser.create_csv()

        # Do the additional codes
        parser = AdditionalCodeParser()
        parser.parse()
        parser.create_csv()

        # Do the foonotes
        parser = FootnoteParser()
        parser.parse()
        parser.create_csv()

        # Do the measures
        parser = MeasureParser("ME")
        parser.parse()
        parser.create_csv()

        # Do the measure exclusions
        parser = MeasureParser("MX")
        parser.parse()
        parser.create_csv()

        return
