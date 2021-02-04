import os
import sys
import csv
import time
import py7zr

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
from classes_gen.measure_component import MeasureComponent
from classes_gen.measure_type import MeasureType
from classes_gen.seasonal_rate import SeasonalRate
from classes_gen.supplementary_unit import SupplementaryUnit
from classes_gen.geographical_area import GeographicalArea
from classes_gen.commodity_footnote import CommodityFootnote
from classes_gen.simplified_procedure_value import SimplifiedProcedureValue
from classes_gen.measure_excluded_geographical_area import MeasureExcludedGeographicalArea


class Application(object):
    def __init__(self):
        self.get_folders()
        load_dotenv('.env')
        self.DATABASE_UK = os.getenv('DATABASE_UK')
        self.WRITE_MEASURES = int(os.getenv('WRITE_MEASURES'))
        self.WRITE_ADDITIONAL_CODES = int(os.getenv('WRITE_ADDITIONAL_CODES'))
        self.WRITE_FOOTNOTES = int(os.getenv('WRITE_FOOTNOTES'))
        self.SNAPSHOT_DATE = os.getenv('SNAPSHOT_DATE')
        self.COMPARISON_DATE = datetime.strptime(os.getenv('COMPARISON_DATE'), '%Y-%m-%d')
        self.mfns = {}

    def create_icl_vme(self):
        self.get_reference_data()
        self.get_footnotes()
        self.get_commodity_footnotes()
        self.open_extract()
        self.get_commodities()
        self.write_footnotes()
        self.close_extract()
        self.zip_extract()

    def get_commodities(self):
        for i in range(0, 10):
        # for i in range(0, 1):
            self.commodities = []
            tic = time.perf_counter()
            print("\nDEALING WITH COMMODITY CODES STARTING WITH " + str(i))
            if self.WRITE_MEASURES == 1:
                self.get_measure_components(i)
                self.get_measure_conditions(i)
                self.get_measure_excluded_geographical_areas(i)
                self.get_measures(i)
                self.categorise_and_sort_measures()
                self.assign_measure_components()
                self.assign_measure_excluded_geographical_areas()
                self.create_measure_duties()

            iteration = str(i) + "%"
            sql = "select * from utils.goods_nomenclature_export_new('" + \
                iteration + "', '" + self.SNAPSHOT_DATE + "') order by 2, 3"
            d = Database()
            rows = d.run_query(sql)
            for row in rows:
                commodity = Commodity()
                commodity.COMMODITY_CODE = row[1]
                if commodity.COMMODITY_CODE[0:2] not in ('98', '99'):
                    if commodity.COMMODITY_CODE == '9702000090':
                        a = 1
                    commodity.goods_nomenclature_sid = row[0]
                    commodity.productline_suffix = row[2]
                    commodity.validity_start_date = row[3]
                    commodity.COMMODITY_EDATE = self.YYYYMMDD(row[3])
                    commodity.COMMODITY_LDATE = self.YYYYMMDD(row[4])
                    commodity.description = row[5]
                    commodity.number_indents = int(row[6])
                    commodity.leaf = row[9]
                    commodity.significant_digits = row[10]
                    commodity.determine_commodity_type()
                    commodity.get_amendment_status()
                    self.commodities.append(commodity)

            if self.WRITE_MEASURES == 1:
                self.assign_measures()

            if self.WRITE_FOOTNOTES == 1:
                self.assign_commodity_footnotes()
            self.build_commodity_hierarchy()

            for commodity in self.commodities:
                commodity.apply_commodity_inheritance()
                commodity.sort_inherited_measures()
                commodity.get_additional_code_indicator()
                commodity.apply_seasonal_rates(self.seasonal_rates)
                commodity.get_end_use()
                commodity.get_supplementary_units(self.supplementary_units)
                commodity.get_spv(self.spvs)
                
            for commodity in self.commodities:
                commodity.create_extract_line()
            
            toc = time.perf_counter()
            self.write_commodities()
            print(f"Ran in {toc - tic:0.2f} seconds")

    def categorise_and_sort_measures(self):
        priority_lookup =  {
            "103": 0,
            "105": 1,
            "306": 2,
            "305": 3,
            "142": 4,
            "145": 4,
            "122": 5,
            "123": 5,
            "143": 5,
            "146": 5,
            "112": 6,
            "115": 6,
            "117": 6,
            "119": 6,
            "551": 7,
            "552": 7,
            "553": 7,
            "554": 7
        }
        for measure in self.measures:
            priority = 99
            try:
                priority = priority_lookup[measure.measure_type_id]
            except:
                priority = 99
            measure.priority = priority

        self.measures.sort(key=lambda x: x.geographical_area_id, reverse=False)
        self.measures.sort(key=lambda x: x.priority, reverse=False)

    
    def assign_measure_components(self):
        print("Assigning measure components")
        measure_count = len(self.measures)
        start_pos = 0
        for measure_component in self.measure_components:
            # for i in range(start_pos, measure_count):
            #     measure = self.measures[i]
            #     if measure.measure_sid == measure_component.measure_sid:
            #         measure.measure_components.append(measure_component)
            #         start_pos = i
            #         break
                
            for measure in self.measures:
                if measure.measure_sid == measure_component.measure_sid:
                    measure.measure_components.append(measure_component)
                    break

    def assign_measure_conditions(self):
        # This is used for working out if there is a chance that the headingg is ex head
        # If there is a 'Y' condition, then this typically means that there are exclusions
        print("Assigning measure conditions")

        for measure_condition in self.measure_conditions_exemption:
            for measure in self.measures:
                if measure.measure_sid == measure_condition.measure_sid:
                    measure.CMDTY_MEASURE_EX_HEAD_IND = "Y"
                    break
                
        for measure_condition in self.measure_conditions_licence:
            for measure in self.measures:
                if measure.measure_sid == measure_condition.measure_sid:
                    measure.FREE_CIRC_DOTI_REQD_IND = "Y"
                    break

    def assign_measure_excluded_geographical_areas(self):
        print("Assigning measure excluded geographical areas")
        for measure_excluded_geographical_area in self.measure_excluded_geographical_areas:
            for measure in self.measures:
                if measure.measure_sid == measure_excluded_geographical_area.measure_sid:
                    measure.measure_excluded_geographical_areas.append(measure_excluded_geographical_area)
                    break

    def create_measure_duties(self):
        print("Creating measure duties")
        for measure in self.measures:
            measure.create_measure_duties()
            measure.create_extract_line_per_geography()
    
    def assign_measures(self):
        print("Assigning measures")
        for measure in self.measures:
            for commodity in self.commodities:
                if commodity.productline_suffix == "80":
                    if measure.goods_nomenclature_item_id == commodity.COMMODITY_CODE:
                        commodity.measures.append(measure)
                        break
                    
    def get_measure_conditions(self, iteration):
        print("Getting measure conditions")
        self.measure_conditions_exemption = []
        self.measure_conditions_licence = []

        # Get exemptions
        sql = """
        select distinct (m.measure_sid)
        from measure_conditions mc, measures m
        where m.measure_sid = mc.measure_sid 
        and mc.certificate_type_code = 'Y'
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        """
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            self.measure_conditions_exemption.append(row[0])
        
        # Get licence requirement
        sql = """
        select distinct (m.measure_sid)
        from measure_conditions mc, measures m
        where m.measure_sid = mc.measure_sid 
        and mc.certificate_type_code in ('D', '9', 'A', 'C', 'D', 'H', 'I', 'L', 'N', 'U', 'Z')
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        """
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            self.measure_conditions_licence.append(row[0])
                
    def get_measure_components(self, iteration):
        print("Getting measure components")
        self.measure_components = []
        sql = """select mc.measure_sid, mc.duty_expression_id, mc.duty_amount, mc.monetary_unit_code,
        mc.measurement_unit_code, mc.measurement_unit_qualifier_code, m.goods_nomenclature_item_id
        from measure_components mc, utils.measures_real_end_dates m
        where m.measure_sid = mc.measure_sid 
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by m.goods_nomenclature_item_id, m.measure_sid, mc.duty_expression_id;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            measure_component = MeasureComponent()
            measure_component.measure_sid = row[0]
            measure_component.duty_expression_id = row[1]
            measure_component.duty_amount = row[2]
            measure_component.monetary_unit_code = row[3]
            measure_component.measurement_unit_code = row[4]
            measure_component.measurement_unit_qualifier_code = row[5]
            measure_component.goods_nomenclature_item_id = row[6]
            measure_component.get_cts_component_definition()
            
            self.measure_components.append(measure_component)
        
    def get_measure_excluded_geographical_areas(self, iteration):
        print("Getting measure excluded geographical areas")
        self.measure_excluded_geographical_areas = []
        sql = """select mega.measure_sid, mega.excluded_geographical_area, mega.geographical_area_sid 
        from measure_excluded_geographical_areas mega, utils.measures_real_end_dates m
        where m.measure_sid = mega.measure_sid 
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by mega.measure_sid, mega.excluded_geographical_area;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            measure_excluded_geographical_area = MeasureExcludedGeographicalArea()
            measure_excluded_geographical_area.measure_sid = row[0]
            measure_excluded_geographical_area.excluded_geographical_area = row[1]
            measure_excluded_geographical_area.geographical_area_sid = row[2]

            self.measure_excluded_geographical_areas.append(measure_excluded_geographical_area)

    def get_measures(self, iteration):
        print("Getting measures")
        self.measures = []
        sql = """select m.*, mt.measure_type_series_id,
        mt.measure_component_applicable_code, mt.trade_movement_code
        from utils.measures_real_end_dates m, measure_types mt
        where m.measure_type_id = mt.measure_type_id
        and left(goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date >= '""" + self.SNAPSHOT_DATE + """')
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
            measure.measure_type_series_id = row[20]
            measure.measure_component_applicable_code = int(row[21])
            measure.trade_movement_code = row[22]
            measure.get_import_export()
            
            measure.expand_raw_data(self.measure_types, self.geographical_areas)

            self.measures.append(measure)

    def write_measures(self):
        print("Writing measures")
        barred_series = ['E', 'F', 'G', 'H', 'K', 'L', 'M', "N", "O", "R", "S", "Z"]
        for measure in self.measures:
            if measure.measure_type_series_id not in barred_series:
                if measure.found_measure_type == True:
                    self.extract_file.write(measure.extract_line)

    def rebase_chapters(self):
        print("Rebasing chapters")
        for commodity in self.commodities:
            if commodity.significant_digits == 2:
                commodity.number_indents = -1
    
    def build_commodity_hierarchy(self):
        self.rebase_chapters()
        print("Building commodity hierarchy")
        commodity_count = len(self.commodities)
        for loop in range(0, commodity_count):
            commodity = self.commodities[loop]
            if commodity.leaf == "1":
                current_indent = commodity.number_indents
                for loop2 in range(loop - 1, -1, -1):
                    commodity2 = self.commodities[loop2]
                    if commodity2.number_indents < current_indent:
                        commodity.hierarchy.append(commodity2)
                        current_indent = commodity2.number_indents
                    if commodity2.number_indents == -1:
                        break
                commodity.hierarchy.reverse()
                commodity.build_hierarchy_string()

            pass
        pass

    def write_commodities(self):
        print("Writing commmodities")
        barred_series = ['E', 'F', 'G', 'H', 'K', 'L', 'M', "N", "O", "R", "S", "Z"]
        self.write_commodity_header()
        self.commodity_count = 0
        self.additional_code_count = 0
        self.measure_count = 0
        for commodity in self.commodities:
            if commodity.leaf == "1":
            # if commodity.leaf == "1" or (commodity.significant_digits == 8 and commodity.productline_suffix == "80"):
                self.commodity_count += 1
                self.extract_file.write(commodity.extract_line)
                if self.WRITE_ADDITIONAL_CODES == 1:
                    if commodity.additional_code_string != "":
                        self.additional_code_count += 1
                        self.extract_file.write(commodity.additional_code_string)

                if self.WRITE_MEASURES == 1:
                    for measure in commodity.measures_inherited:
                        if measure.measure_type_series_id not in barred_series:
                            self.measure_count += measure.line_count
                            self.extract_file.write(measure.extract_line)

        self.write_commodity_footer()

    def get_folders(self):
        self.current_folder = os.getcwd()
        self.data_folder = os.path.join(self.current_folder, "data")
        self.data_in_folder = os.path.join(self.data_folder, "in")
        self.data_out_folder = os.path.join(self.data_folder, "out")
        self.icl_vme_folder = os.path.join(self.data_folder, "icl_vme")
        self.reference_folder = os.path.join(self.data_folder, "reference")

    def open_extract(self):
        date_time_obj = datetime.strptime(self.SNAPSHOT_DATE, '%Y-%m-%d')
        year = date_time_obj.strftime("%Y")
        month = date_time_obj.strftime("%b").lower()
        if CommonString.divider == "|":
            self.filename = "hmrc-tariff-ascii-" + month + "-" + year + "-piped.txt"
        else:
            self.filename = "hmrc-tariff-ascii-" + month + "-" + year + ".txt"
        
        self.filepath = os.path.join(self.icl_vme_folder, self.filename)
        self.extract_file = open(self.filepath, "w+")

    def close_extract(self):
        self.extract_file.close()
        
    def zip_extract(self):
        self.zipfile = self.filepath.replace(".txt", ".7z")
        try:
            os.remove(self.zipfile)
        except:
            pass
        with py7zr.SevenZipFile(self.zipfile, 'w') as archive:
            archive.write(self.filepath, self.filename)
        pass
        
    def get_commodity_footnotes(self):
        print("Getting commodity-level footnote associations")
        self.commodity_footnotes = []
        self.commodities_with_footnotes = []
        sql = """select gn.goods_nomenclature_item_id, gn.goods_nomenclature_sid,
        fagn.footnote_type as footnote_type_id, fagn.footnote_id 
        from  footnote_association_goods_nomenclatures fagn, goods_nomenclatures gn 
        where  fagn.goods_nomenclature_sid = gn.goods_nomenclature_sid 
        and fagn.validity_end_date is null 
        and gn.validity_end_date is null
        order by gn.goods_nomenclature_item_id, fagn.footnote_type, fagn.footnote_id;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            footnote = CommodityFootnote()
            footnote.goods_nomenclature_item_id = row[0]
            footnote.goods_nomenclature_sid = row[1]
            footnote.footnote_type_id = row[2]
            footnote.footnote_id = row[3]
            footnote.get_footnote_number()
            self.commodity_footnotes.append(footnote)
            self.commodities_with_footnotes.append(footnote.goods_nomenclature_sid)
            
        self.commodities_with_footnotes = set(self.commodities_with_footnotes)

    def assign_commodity_footnotes(self):
        print("Starting footnote assignment")
        for footnote_association in self.commodity_footnotes:
            for commodity in self.commodities:
                if footnote_association.goods_nomenclature_sid == commodity.goods_nomenclature_sid:
                    commodity.footnotes.append(footnote_association)
                    break
                
        for commodity in self.commodities:
            commodity.append_footnotes_to_description()
        
        print("Ending footnote assignment")
    
    def get_footnotes(self):
        # Problem with footnotes is the size of the fields
        # They are identified by 5 digits in the TAP / CDS feed
        # but only by three in the data from CHIEF - therefore we need a kludge massage:
        # The answer is
        # Any footnotes beginning with NC - add 800 to the IDs:
        # Any footnotes beginning with PN - add 900 to the IDs:
        # Any footnotes beginning with TN - as-is
        # This gets round the possible duplication on the three digits:

        print("Getting footnotes")
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
            footnote.footnote_type_id = row[0]
            footnote.footnote_id = row[1]
            footnote.RECORD_TYPE = "FN"
            footnote.FOOTNOTE_EDATE = self.YYYYMMDD(row[3])
            footnote.FOOTNOTE_LDATE = self.YYYYMMDD(row[4])
            footnote.FOOTNOTE_TEXT = row[2]
            footnote.get_footnote_number()
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

    def write_footnote_footer(self):
        # CF0000120
        # RECORD-TYPE 2
        # FOOTNOTE-RECORD-COUNT 7
        self.footnote_footer = "CF"
        self.footnote_footer += str(len(self.footnotes)).zfill(7)
        self.extract_file.write(self.footnote_footer)

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
        
    def write_commodity_footer(self):
        """
        CO0018494000128803435560000000000342100000366759
        CO
        0018494
        0001288
        0343556
        0000000
        0003421
        00000366759

        CM-RECORD-COUNT	7	9(7)
        CA-RECORD-COUNT	7	9(7)
        ME-RECORD-COUNT	7	9(7)
        MD-RECORD-COUNT	7	9(7)
        MX-RECORD-COUNT	7	9(7)
        TOTAL-RECORD-COUNT	11	9(11)
        """
        
        self.measure_exception_count = 0
        total_record_count = self.commodity_count + self.additional_code_count + self.measure_count + self.measure_exception_count
        
        CM_RECORD_COUNT = str(self.commodity_count).rjust(7, "0")
        CA_RECORD_COUNT = str(self.additional_code_count).rjust(7, "0")
        ME_RECORD_COUNT = str(self.measure_count).rjust(7, "0")
        MD_RECORD_COUNT = "0000000"
        MX_RECORD_COUNT = "0000000"
        TOTAL_RECORD_COUNT = str(total_record_count).rjust(11, "0")

        self.commodity_footer = "CO"
        self.commodity_footer += CM_RECORD_COUNT
        self.commodity_footer += CA_RECORD_COUNT
        self.commodity_footer += ME_RECORD_COUNT
        self.commodity_footer += MD_RECORD_COUNT
        self.commodity_footer += MX_RECORD_COUNT
        self.commodity_footer += TOTAL_RECORD_COUNT
        
        self.extract_file.write(self.commodity_footer)
        

    def write_footnotes(self):
        if self.WRITE_FOOTNOTES == 1:
            print("Writing footnotes")
            self.write_footnote_header()
            for footnote in self.footnotes:
                self.extract_file.write(footnote.extract_line)
            self.write_footnote_footer()

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
        self.get_seasonal_rates()
        self.get_spvs()
        self.get_geographical_areas()
        self.get_supplementary_units_reference()

    def get_measure_types(self):
        print("Getting measure types")
        self.measure_types = []
        filename = os.path.join(self.reference_folder, "measure_types.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) >= 4:
                    measure_type = MeasureType(row[0], row[1], row[2], row[3])
                    self.measure_types.append(measure_type)

    def get_seasonal_rates(self):
        # Read the seasonal rates from the reference CSV and load to a global list
        print("Getting seasonal rates")
        self.seasonal_rates = []
        filename = os.path.join(self.reference_folder, "seasonal_rates.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                seasonal_rate = SeasonalRate(row[0], row[1], row[2], row[3], row[4])
                self.seasonal_rates.append(seasonal_rate)

    def get_spvs(self):
        print("Getting SPVs")
        self.spvs = []
        filename = os.path.join(self.reference_folder, "spvs.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                spv = SimplifiedProcedureValue(row[0], row[1])
                self.spvs.append(spv)

    def get_supplementary_units_reference(self):
        print("Getting supplementary units")
        self.supplementary_units = []
        self.supplementary_unit_dict = {}
        filename = os.path.join(self.reference_folder, "supplementary_units.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                supplementary_unit = SupplementaryUnit(row[0], row[1], row[2])
                self.supplementary_units.append(supplementary_unit)
                self.supplementary_unit_dict[row[0]+row[1]] = row[2]

    def get_geographical_areas(self):
        print("Getting geographical areas")
        self.geographical_areas = []
        filename = os.path.join(self.reference_folder, "geographical_areas.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) >= 3:
                    geographical_area = GeographicalArea(row[0], row[1], row[2])
                    self.geographical_areas.append(geographical_area)
