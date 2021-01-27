import os
import sys
import csv

from dotenv import load_dotenv
from datetime import datetime
from classes.additional_code_parser import AdditionalCodeParser
from classes.commodity_parser import CommodityParser
from classes.footnote_parser import FootnoteParser
from classes.measure_parser import MeasureParser
from classes.enums import CommonString

from classes_gen.database import Database
from classes_gen.footnote import Footnote
from classes_gen.commodity import Commodity
from classes_gen.measure import Measure
from classes_gen.measure_type import MeasureType


class Application(object):
    def __init__(self):
        self.get_folders()
        load_dotenv('.env')
        self.DATABASE_UK = os.getenv('DATABASE_UK')
        
    def create_icl_vme(self):
        self.get_reference_data()
        self.open_extract()
        self.get_commodities()
        self.write_commodities()
        # self.get_footnotes()
        # self.write_footnotes()
        self.close_extract()

    def get_commodities(self):
        self.commodities = []
        # for i in range(0, 10):
        for i in range(1, 2):
            self.get_measures(i)
            self.write_measures()
            iteration = str(i) + "%"
            date = "20210201"
            sql = "select * from utils.goods_nomenclature_export_new('" + \
                iteration + "', '" + date + "') order by 2, 3"
            d = Database()
            rows = d.run_query(sql)
            for row in rows:
                commodity = Commodity()
                commodity.goods_nomenclature_sid = row[0]
                commodity.COMMODITY_CODE = row[1]
                commodity.productline_suffix = row[2]
                commodity.COMMODITY_EDATE = self.YYYYMMDD(row[3])
                commodity.COMMODITY_LDATE = self.YYYYMMDD(row[4])
                commodity.description = row[5]
                commodity.number_indents = int(row[6])
                commodity.leaf = row[9]
                commodity.significant_digits = row[10]
                self.commodities.append(commodity)

            self.build_commodity_hierarchy()

            for commodity in self.commodities:
                commodity.create_extract_line()

    def get_measures(self, iteration):
        self.measures = []
        the_date = "20210201"
        sql = """select * from utils.measures_real_end_dates m
        where left(goods_nomenclature_item_id, 1) = '""" + str(iteration) + """'
        and (validity_end_date is null or validity_end_date >= '""" + the_date + """')
        order by goods_nomenclature_item_id, measure_type_id;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            measure = Measure()
            measure.measure_sid = row[0]
            measure.goods_nomenclature_item_id = row[1]
            measure.geographical_area_id = row[2]
            measure.measure_type_id = row[3]
            measure.measure_generating_regulation_id = row[4]
            measure.ordernumber = row[5]
            measure.reduction_indicator = row[6]
            measure.additional_code_type_id = row[7]
            measure.additional_code_id = row[8]
            measure.additional_code = row[9]
            measure.measure_generating_regulation_role = row[10]
            measure.justification_regulation_role = row[11]
            measure.justification_regulation_id = row[12]
            measure.stopped_flag = row[13]
            measure.geographical_area_sid = row[14]
            measure.goods_nomenclature_sid = row[15]
            measure.validity_start_date = row[18]
            measure.validity_end_date = row[19]
            
            measure.expand_raw_data(self.measure_types)
            measure.create_extract_line()

            self.measures.append(measure)

    def write_measures(self):
        # self.write_commodity_header()
        for measure in self.measures:
            self.extract_file.write(measure.extract_line)

    def build_commodity_hierarchy(self):
        commodity_count = len(self.commodities)
        for loop in range(0, commodity_count):
            commodity = self.commodities[loop]
            if commodity.leaf == "1":
                current_indent = commodity.number_indents
                for loop2 in range(loop, -1, -1):
                    commodity2 = self.commodities[loop2]
                    if commodity2.number_indents < current_indent:
                        commodity.hierarchy.append(commodity2)
                        current_indent = commodity2.number_indents
                    if commodity2.number_indents == 0:
                        break
                commodity.hierarchy.reverse()
                commodity.build_hierarchy_string()

            pass
        pass

    def write_commodities(self):
        self.write_commodity_header()
        for commodity in self.commodities:
            if commodity.leaf == "1":
                self.extract_file.write(commodity.extract_line)

    def get_folders(self):
        self.current_folder = os.getcwd()
        self.data_folder = os.path.join(self.current_folder, "data")
        self.data_in_folder = os.path.join(self.data_folder, "in")
        self.data_out_folder = os.path.join(self.data_folder, "out")
        self.icl_vme_folder = os.path.join(self.data_folder, "icl_vme")
        self.reference_folder = os.path.join(self.data_folder, "reference")

    def open_extract(self):
        filename = os.path.join(self.icl_vme_folder,
                                "hmce-tariff-ascii-jan2021.matt")
        self.extract_file = open(filename, "w+")

    def close_extract(self):
        self.extract_file.close()

    def get_footnotes(self):
        self.footnotes = []
        sql = """SELECT f1.footnote_type_id,
        f1.footnote_id, fd1.description,
        f1.validity_start_date, f1.validity_end_date
        FROM footnote_descriptions fd1, footnotes f1, footnote_types ft 
        where f1.footnote_type_id = ft.footnote_type_id 
        and ft.application_code in (1, 2)
        and f1.validity_end_date is null
        and fd1.footnote_id::text = f1.footnote_id::text AND fd1.footnote_type_id::text = f1.footnote_type_id::text AND (fd1.footnote_description_period_sid IN ( SELECT max(ft2.footnote_description_period_sid) AS max
        FROM footnote_descriptions ft2
        WHERE fd1.footnote_type_id::text = ft2.footnote_type_id::text AND fd1.footnote_id::text = ft2.footnote_id::text))
        ORDER BY fd1.footnote_type_id, fd1.footnote_id;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            footnote = Footnote()
            footnote.RECORD_TYPE = "FN"
            footnote.FOOTNOTE_NUMBER = row[0] + row[1]
            footnote.FOOTNOTE_EDATE = self.YYYYMMDD(row[3])
            footnote.FOOTNOTE_LDATE = self.YYYYMMDD(row[4])
            footnote.FOOTNOTE_TEXT = row[2]
            footnote.format_text()
            self.footnotes.append(footnote)

    def write_footnote_header(self):
        # HF2020121500000021001
        # RECORD-TYPE 2
        # DATE-CREATED 8
        # TIME-CREATED 6
        # RUN-NUMBER 5
        self.footnote_header = "HF"
        self.footnote_header += self.YYYYMMDD(datetime.now())
        self.footnote_header += self.HHMMSS(datetime.now())
        self.footnote_header += "21002"
        self.footnote_header += CommonString.line_feed
        self.extract_file.write(self.footnote_header)

    def write_commodity_header(self):
        # HF2020121500000021001
        # RECORD-TYPE 2
        # DATE-CREATED 8
        # TIME-CREATED 6
        # RUN-NUMBER 5
        self.commodity_header = "HE"
        self.commodity_header += self.YYYYMMDD(datetime.now())
        self.commodity_header += self.HHMMSS(datetime.now())
        self.commodity_header += "21002"
        self.commodity_header += CommonString.line_feed
        self.extract_file.write(self.commodity_header)

    def write_footnotes(self):
        self.write_footnote_header()
        for footnote in self.footnotes:
            self.extract_file.write(footnote.extract_line)

    def YYYYMMDD(self, d):
        if d is None:
            return "00000000"
        else:
            ret = d.strftime("%Y%m%d")
            return ret

    def HHMMSS(self, d):
        if d is None:
            return "00000000"
        else:
            ret = d.strftime("%H%M%S")
            return ret

    def parse(self):
        # Do the additional codes
        parser = AdditionalCodeParser()
        parser.parse()
        parser.create_csv()

        # Do the comm codes
        parser = CommodityParser()
        parser.parse()
        parser.create_csv()

        # Do the additional codes
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

    def get_reference_data(self):
        self.get_measure_types()

    def get_measure_types(self):
        self.measure_types = []
        filename = os.path.join(self.reference_folder, "measure_types.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                measure_type = MeasureType(row[0], row[1], row[2])
                self.measure_types.append(measure_type)
