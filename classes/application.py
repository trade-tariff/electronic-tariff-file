import os
import re
import sys
import csv
import time
import py7zr
import ssl
from zipfile import ZipFile
from pathlib2 import Path

from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from classes.additional_code_parser import AdditionalCodeParser
from classes.commodity_parser import CommodityParser
from classes.footnote_parser import FootnoteParser
from classes.measure_parser import MeasureParser
from classes.appender import Appender
from classes.enums import CommonString
from classes.functions import functions as f
from classes.aws_bucket import AwsBucket
from classes.sendgrid_mailer import SendgridMailer
from classes.zipper import Zipper
from classes.delta import Delta


from classes_gen.database import Database
from classes_gen.footnote import Footnote
from classes_gen.certificate import Certificate
from classes_gen.quota_definition import QuotaDefinition, QuotaExclusion, QuotaCommodity
from classes_gen.commodity import Commodity
from classes_gen.measure import Measure
from classes_gen.measure_component import MeasureComponent
from classes_gen.measure_condition import MeasureCondition
from classes_gen.measure_type import MeasureType, MeasureType2
from classes_gen.additional_code import AdditionalCode
from classes_gen.seasonal_rate import SeasonalRate
from classes_gen.supplementary_unit import SupplementaryUnit
from classes_gen.supplementary_unit import UnmatchedSupplementaryUnit
from classes_gen.geographical_area import GeographicalArea, GeographicalArea2
from classes_gen.commodity_footnote import CommodityFootnote
from classes_gen.simplified_procedure_value import SimplifiedProcedureValue
from classes_gen.measure_excluded_geographical_area import MeasureExcludedGeographicalArea
from classes_gen.footnote_association_measure import FootnoteAssociationMeasure
from classes_gen.pr_measure import PrMeasure
from classes_gen.spv.spv_handler import SPVHandler


class Application(object):
    def __init__(self):
        load_dotenv('.env')

        self.BUCKET_NAME = os.getenv('BUCKET_NAME')
        self.bucket_url = "https://" + self.BUCKET_NAME + ".s3.amazonaws.com/"
        self.WRITE_MEASURES = int(os.getenv('WRITE_MEASURES'))
        self.WRITE_ADDITIONAL_CODES = int(os.getenv('WRITE_ADDITIONAL_CODES'))
        self.WRITE_FOOTNOTES = int(os.getenv('WRITE_FOOTNOTES'))
        self.WRITE_ANCILLARY_FILES = int(os.getenv('WRITE_ANCILLARY_FILES'))
        self.DEBUG_OVERRIDE = int(os.getenv('DEBUG_OVERRIDE'))
        self.PLACEHOLDER_FOR_EMPTY_DESCRIPTIONS = os.getenv('PLACEHOLDER_FOR_EMPTY_DESCRIPTIONS')
        self.VSCODE_DEBUG_MODE = os.getenv('VSCODE_DEBUG_MODE')

        self.mfns = {}

        # Check whether UK or XI
        if ("dest" not in sys.argv[0]):
            self.get_scope()
        else:
            self.scope = "uk"

        # Date of the report
        self.get_date()

        self.get_folders()
        self.get_process_scope()
        self.message_string = ""
        self.create_ssl_unverified_context()

    def create_ssl_unverified_context(self):
        ssl._create_default_https_context = ssl._create_unverified_context

    def get_excluded_sids(self):
        load_dotenv('.env')
        self.excluded_sids = os.getenv('EXCLUDED_SIDS')
        a = 1

    def create_icl_vme(self):
        self.get_excluded_sids()
        self.get_reference_data()
        self.get_footnotes()
        self.get_commodity_footnotes()
        self.open_extract()
        self.write_commodity_header()
        self.get_commodities()
        self.write_footnotes()

        if self.WRITE_ANCILLARY_FILES == 1:
            self.get_all_footnotes()
            self.get_all_certificates()
            self.get_all_quotas()
            self.get_all_geographies()
            self.get_all_measure_types()
            self.get_all_additional_codes()

        self.close_extract()
        self.count_measures()

        self.create_delta()

        # Only compress, upload and email when we have DEBUG_OVERRIDE switched on
        # if self.DEBUG_OVERRIDE == 1 or self.VSCODE_DEBUG_MODE == False:
        if 1 > 0:
            self.zip_and_upload()
            self.create_email_message()
            self.send_email_message()

        self.write_log()

    def write_log(self):
        f = open(self.log_filename, "w")
        f.write(self.message_string)

    def count_measures(self):
        self.start_timer("Counting measures and updating counts in ICL VME file")
        self.measure_count = 0
        self.measure_exception_count = 0
        with open(self.filepath_icl_vme) as fp:
            line = fp.readline()
            while line:
                if line[0:2] == "ME":
                    self.measure_count += 1
                elif line[0:2] == "MX":
                    self.measure_exception_count += 1

                line = fp.readline()
        fp.close()

        self.TOTAL_RECORD_COUNT = 0
        self.TOTAL_RECORD_COUNT += self.commodity_count
        self.TOTAL_RECORD_COUNT += self.additional_code_count
        self.TOTAL_RECORD_COUNT += self.measure_count
        self.TOTAL_RECORD_COUNT += self.measure_exception_count

        path = Path(self.filepath_icl_vme)
        text = path.read_text()
        text = text.replace("ME_RECORD_COUNT", str(self.measure_count).rjust(7, "0"))
        text = text.replace("MX_RECORD_COUNT", str(self.measure_exception_count).rjust(7, "0"))
        text = text.replace("TOTAL_RECORD_COUNT", str(self.TOTAL_RECORD_COUNT).rjust(11, "0"))
        path.write_text(text)

        self.end_timer("Counting measures and updating counts in ICL VME file")

    def get_date(self):
        if len(sys.argv) > 4:
            d = sys.argv[4].lower()
            date_format = "%Y-%m-%d"
            try:
                datetime.strptime(d, date_format)
                self.SNAPSHOT_DATE = d
                self.COMPARISON_DATE = datetime.strptime(d, '%Y-%m-%d') - timedelta(days=7)
            except ValueError:
                print("This is the incorrect date string format. It should be YYYY-MM-DD")
                sys.exit()
        else:
            d = datetime.now()
            self.SNAPSHOT_DATE = d.strftime('%Y-%m-%d')
            self.COMPARISON_DATE = d - timedelta(days=7)

    def get_scope(self):
        # Takes arguments from the command line to identify
        # whether to process UK or EU data
        if len(sys.argv) > 1:
            self.scope = sys.argv[1].lower()
        else:
            print("Please specify the country scope (uk or xi)")
            sys.exit()

        if self.scope not in ("uk", "xi"):
            print("Please specify the country scope (uk or xi)")
            sys.exit()

        load_dotenv('.env')
        if self.scope == "uk":
            self.DATABASE = os.getenv('DATABASE_UK')
        else:
            self.DATABASE = os.getenv('DATABASE_EU')

    def get_process_scope(self):
        # Takes arguments from the command line to identify
        # which commodities to process
        if len(sys.argv) > 2:
            self.start = int(sys.argv[2])
            if len(sys.argv) > 3:
                self.end = int(sys.argv[3])
            else:
                self.end = 10
        else:
            self.start = 0
            self.end = 10

    def get_commodities(self):
        # These need to be set at the start before any of the runs, and not reset by the runs
        self.commodity_count = 0
        self.additional_code_count = 0
        self.measure_count = 0
        self.measure_exception_count = 0

        self.commodities_dict = {}

        for i in range(self.start, self.end):
            self.start_loop_timer("Creating data for commodity codes starting with " + str(i))
            self.commodities = []
            self.get_measure_components(i)
            self.get_measure_conditions(i)
            self.get_measure_excluded_geographical_areas(i)
            self.get_footnote_association_measures(i)
            self.get_measures(i)
            self.categorise_measures()
            self.assign_measure_components_to_measures()
            self.assign_measure_conditions_to_measures()
            self.assign_measure_excluded_geographical_areas()
            self.assign_footnote_associations_to_measures()
            self.sort_measures_by_commodity_code()
            self.create_measure_duties()
            self.valid_descriptions = self.get_latest_valid_descriptions(i)
            self.valid_descriptions_xi = self.get_latest_valid_descriptions(i, "xi")

            iteration = str(i) + "%"
            self.get_recent_descriptions(str(i))

            sql = """select goods_nomenclature_sid, goods_nomenclature_item_id, producline_suffix,
            validity_start_date, validity_end_date, description, number_indents, chapter, node,
            leaf, significant_digits
            from utils.goods_nomenclature_export_new(%s, %s)
            where goods_nomenclature_sid not in (""" + self.excluded_sids + """)
            order by 2, 3"""

            d = Database()
            params = [
                iteration,
                self.SNAPSHOT_DATE
            ]
            rows = d.run_query(sql, params)
            for row in rows:
                commodity = Commodity()
                commodity.COMMODITY_CODE = row[1]
                if commodity.COMMODITY_CODE[0:2] not in ('98', '99'):
                    commodity.goods_nomenclature_sid = row[0]
                    commodity.productline_suffix = row[2]
                    commodity.validity_start_date = row[3]
                    commodity.validity_end_date = row[4]
                    commodity.COMMODITY_EDATE = self.YYYYMMDD(row[3])
                    commodity.COMMODITY_LDATE = self.YYYYMMDD(row[4])
                    commodity.description = row[5]
                    commodity.number_indents = int(row[6])
                    commodity.leaf = int(str(row[9]))
                    commodity.significant_digits = int(row[10])
                    commodity.determine_imp_exp_use()
                    commodity.determine_commodity_type()
                    commodity.get_amendment_status()
                    commodity.cleanse_description()
                    self.commodities.append(commodity)

                    if commodity.productline_suffix == "80":
                        self.commodities_dict[commodity.COMMODITY_CODE] = commodity.description

            self.assign_measures_to_commodities()

            self.assign_commodity_footnotes()
            self.build_commodity_hierarchy()

            self.start_timer("Applying inheritance etc.")
            f = open("comm_codes.txt", "w")
            for commodity in self.commodities:
                commodity.apply_commodity_inheritance()
                commodity.sort_inherited_measures()

                commodity.get_additional_code_indicator()
                commodity.apply_seasonal_rates(self.seasonal_rates)
                commodity.get_end_use()
                if commodity.COMMODITY_CODE == "1515905900":
                    a = 1
                commodity.get_supplementary_units(self.supplementary_units)
                commodity.get_spv(self.spvs)

            self.end_timer("Applying inheritance etc.")

            # Bubble up the VAT and excise measures from down below
            self.start_timer("Bubble up VAT and excise")
            commodity_count = len(self.commodities)
            for loop in range(0, commodity_count - 1):
                commodity = self.commodities[loop]
                if commodity.pseudo_line is True:
                    for loop2 in range(loop + 1, commodity_count - 1):
                        commodity2 = self.commodities[loop2]
                        if commodity.COMMODITY_CODE[0:4] != commodity2.COMMODITY_CODE[0:4]:
                            # Break out if we have moved on to a different heading
                            break

                        for item in commodity2.hierarchy:
                            if item.COMMODITY_CODE == commodity.COMMODITY_CODE:
                                for m in commodity2.measures:
                                    inheritable_measure_types = ["103", "105", "305", "306"]
                                    if m.measure_type_id in inheritable_measure_types:
                                        found = False
                                        for m2 in commodity.measures_inherited:
                                            if m2.measure_type_id == m.measure_type_id:
                                                if m2.additional_code_id == m.additional_code_id:
                                                    found = True
                                                    break
                                        if found is False:
                                            commodity.measures_inherited.append(m)

            self.end_timer("Bubble up VAT and excise")

            self.start_timer("Creating extract lines")
            for commodity in self.commodities:
                commodity.create_extract_line()
            self.end_timer("Creating extract lines")

            self.write_commodities()

            self.end_loop_timer("\nDEALING WITH COMMODITY CODES STARTING WITH " + str(i) + "\n")

        self.write_commodity_footer()

    def get_latest_valid_descriptions(self, iteration, scope_override=None):
        tmp = {}
        sql = """
        with cte as (
        select distinct on (gnd.goods_nomenclature_sid)
        gndp.goods_nomenclature_sid, gndp.goods_nomenclature_item_id, gndp.productline_suffix, gnd.description
        from goods_nomenclature_description_periods gndp, goods_nomenclature_descriptions gnd
        where gndp.goods_nomenclature_sid = gnd.goods_nomenclature_sid
        and left(gnd.goods_nomenclature_item_id, 1) = %s
        and gndp.validity_start_date <= %s
        and gnd.description is not null
        order by gnd.goods_nomenclature_sid, gndp.validity_start_date desc, gnd.goods_nomenclature_item_id
        )
        select (goods_nomenclature_item_id || productline_suffix) as code, description
        from cte order by goods_nomenclature_item_id, productline_suffix;
        """
        params = [
            str(iteration),
            self.SNAPSHOT_DATE
        ]
        d = Database(scope_override)
        rows = d.run_query(sql, params)
        if len(rows) > 0:
            for row in rows:
                tmp[row[0]] = row[1]

        return (tmp)

    def sort_measures_by_commodity_code(self):
        self.start_timer("Sorting commodity codes")
        self.measures.sort(key=lambda x: (x.additional_code_id is None, x.additional_code_id), reverse=False)
        self.measures.sort(key=lambda x: (x.additional_code_type_id is None, x.additional_code_type_id), reverse=False)
        self.measures.sort(key=lambda x: (x.ordernumber is None, x.ordernumber), reverse=False)
        self.measures.sort(key=lambda x: x.geographical_area_id, reverse=False)
        self.measures.sort(key=lambda x: x.priority, reverse=False)
        self.measures.sort(key=lambda x: x.goods_nomenclature_item_id, reverse=False)
        self.end_timer("Sorting commodity codes")

    def start_timer(self, msg):
        self.tic = time.perf_counter()
        # msg = msg.upper() + "\n - Starting"
        msg = msg.upper()
        print(msg)
        self.message_string += msg + "\n"

    def end_timer(self, msg):
        self.toc = time.perf_counter()
        msg = " - Completed in " + "{:.1f}".format(self.toc - self.tic) + " seconds\n"
        print(msg)
        self.message_string += msg + "\n"

    def start_loop_timer(self, msg):
        self.loop_tic = time.perf_counter()
        # msg = msg.upper() + "\n - Starting"
        msg = msg.upper()
        print(msg + "\n")
        self.message_string += msg + "\n"

    def end_loop_timer(self, msg):
        self.loop_toc = time.perf_counter()
        msg = msg.upper() + " - Completed in " + "{:.1f}".format(self.loop_toc - self.loop_tic) + " seconds\n"
        print(msg + "\n")
        self.message_string += msg + "\n"

    def get_recent_descriptions(self, iteration):
        # This is used to check for amendment status - do not touch
        self.descriptions = []
        sql = """
        select goods_nomenclature_item_id, validity_start_date
        from goods_nomenclature_description_periods gndp
        where productline_suffix = '80'
        and left(goods_nomenclature_item_id, 1) = %s
        and validity_start_date >= '2021-01-01'
        order by 1;
        """
        params = [
            iteration
        ]
        d = Database()
        rows = d.run_query(sql, params)
        if len(rows) > 0:
            self.descriptions = rows
        a = 1

    def categorise_measures(self):
        # Used to set a priority precedence for the measures that appear in
        # the export file(s) - MFNs come first etc.
        priority_lookup = {
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
            "554": 7,
            "695": 8
        }
        for measure in self.measures:
            priority = 99
            try:
                priority = priority_lookup[measure.measure_type_id]
            except Exception as e:
                priority = 99
            measure.priority = priority

    def assign_measure_conditions_to_measures(self):
        # This is used for working out if there is a chance that the heading is ex head
        # If there is a 'Y' condition, then this typically means that there are exclusions
        self.start_timer("Assigning measure conditions to measures")

        start_point = 0
        for measure_condition in self.measure_conditions:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == measure_condition.measure_sid:
                    start_point = i
                    measure.measure_conditions.append(measure_condition)
                    break

        start_point = 0
        for measure_condition in self.measure_conditions_exemption:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == measure_condition:
                    start_point = i
                    measure.CMDTY_MEASURE_EX_HEAD_IND = "Y"
                    break

        start_point = 0
        for measure_condition in self.measure_conditions_licence:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == measure_condition:
                    start_point = i
                    measure.FREE_CIRC_DOTI_REQD_IND = "Y"
                    break

        self.end_timer("Assigning measure conditions to measures")

    def assign_measure_components_to_measures(self):
        # Assign the measure components to the measures
        self.start_timer("Assigning measure components to measures")
        start_point = 0
        for measure_component in self.measure_components:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == measure_component.measure_sid:
                    start_point = i
                    measure.measure_components.append(measure_component)
                    break

        self.end_timer("Assigning measure components to measures")

    def assign_measure_excluded_geographical_areas(self):
        # Assign measure exclusions to measures
        self.start_timer("Assigning measure excluded geographical areas to measures")
        start_point = 0
        for measure_excluded_geographical_area in self.measure_excluded_geographical_areas:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == measure_excluded_geographical_area.measure_sid:
                    start_point = i
                    measure.measure_excluded_geographical_areas.append(measure_excluded_geographical_area)
                    break

        self.end_timer("Assigning measure excluded geographical areas to measures")

    def assign_footnote_associations_to_measures(self):
        # Assign footnote_association_measures
        self.start_timer("Assigning footnotes to measures")
        start_point = 0
        for footnote_association_measure in self.footnote_association_measures:
            for i in range(start_point, len(self.measures)):
                measure = self.measures[i]
                if measure.measure_sid == footnote_association_measure.measure_sid:
                    start_point = i
                    measure.footnote_association_measures.append(footnote_association_measure)
                    break

        # Now create a string from the associations per measure.
        # Start by sorting the footnotes alphabetically
        for measure in self.measures:
            measure.footnote_association_measures.sort(key=lambda x: x.footnote_id, reverse=False)
            measure.footnote_association_measures.sort(key=lambda x: x.footnote_type_id, reverse=False)
            measure.footnote_string = ""
            for footnote_association_measure in measure.footnote_association_measures:
                measure.footnote_string += footnote_association_measure.footnote_type_id + footnote_association_measure.footnote_id + "|"
            measure.footnote_string = measure.footnote_string.strip("|")

        self.end_timer("Assigning footnotes to measures")

    def create_measure_duties(self):
        self.start_timer("Creating measure duties")
        for measure in self.measures:
            measure.create_measure_duties()
            measure.create_extract_line_per_geography()

        self.end_timer("Creating measure duties")

    def assign_measures_to_commodities(self):
        self.start_timer("Assigning measures to commodities")
        start_point = 0
        for measure in self.measures:
            for i in range(start_point, len(self.commodities)):
                commodity = self.commodities[i]
                if commodity.productline_suffix == "80":
                    if measure.goods_nomenclature_item_id == commodity.COMMODITY_CODE:
                        start_point = i
                        commodity.measures.append(measure)
                        break

        self.end_timer("Assigning measures to commodities")

    def get_measure_conditions(self, iteration):
        self.start_timer("Getting measure conditions")
        self.measure_conditions = []
        self.measure_conditions_exemption = []
        self.measure_conditions_licence = []

        # First, get all measure conditions - these are needed to add to the CSV version of the file
        sql = """
        select mc.measure_condition_sid, mc.measure_sid, mc.condition_code, mc.component_sequence_number,
        mc.condition_duty_amount, mc.condition_monetary_unit_code, mc.condition_measurement_unit_code,
        mc.condition_measurement_unit_qualifier_code, mc.action_code, mc.certificate_type_code, mc.certificate_code
        from measure_conditions mc, utils.materialized_measures_real_end_dates m
        where m.measure_sid = mc.measure_sid
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by mc.measure_sid, mc.condition_code, mc.component_sequence_number
        """
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            mc = MeasureCondition()
            mc.measure_condition_sid = row[0]
            mc.measure_sid = row[1]
            mc.condition_code = row[2]
            mc.component_sequence_number = row[3]
            mc.condition_duty_amount = row[4]
            mc.condition_monetary_unit_code = row[5]
            mc.condition_measurement_unit_code = row[6]
            mc.condition_measurement_unit_qualifier_code = row[7]
            mc.action_code = row[8]
            mc.certificate_type_code = row[9]
            mc.certificate_code = row[10]
            self.measure_conditions.append(mc)

            if mc.certificate_type_code == "Y":
                # Second, get the exemption type records - these are needed to do ...
                self.measure_conditions_exemption.append(mc.measure_sid)
            elif mc.certificate_type_code in ('D', '9', 'A', 'C', 'D', 'H', 'I', 'L', 'N', 'U', 'Z'):
                # Get licence requirement
                self.measure_conditions_licence.append(mc.measure_sid)

        self.measure_conditions_exemption = list(set(self.measure_conditions_exemption))
        self.measure_conditions_licence = list(set(self.measure_conditions_licence))

        self.end_timer("Getting measure conditions")

    def get_measure_components(self, iteration):
        # Get measure components
        self.start_timer("Getting measure components")
        self.measure_components = []
        sql = """select mc.measure_sid, mc.duty_expression_id, mc.duty_amount, mc.monetary_unit_code,
        mc.measurement_unit_code, mc.measurement_unit_qualifier_code, m.goods_nomenclature_item_id
        from measure_components mc, utils.materialized_measures_real_end_dates m
        where m.measure_sid = mc.measure_sid
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by m.measure_sid, mc.duty_expression_id;"""
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

        self.end_timer("Getting measure components")

    def get_measure_excluded_geographical_areas(self, iteration):
        # Get measure geo exclusions
        self.start_timer("Getting measure excluded geographical areas")
        self.measure_excluded_geographical_areas = []
        sql = """select mega.measure_sid, mega.excluded_geographical_area, mega.geographical_area_sid
        from measure_excluded_geographical_areas mega, utils.materialized_measures_real_end_dates m
        where m.measure_sid = mega.measure_sid
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        and mega.excluded_geographical_area != 'EU'
        order by mega.measure_sid, mega.excluded_geographical_area;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            measure_excluded_geographical_area = MeasureExcludedGeographicalArea()
            measure_excluded_geographical_area.measure_sid = row[0]
            measure_excluded_geographical_area.excluded_geographical_area = row[1]
            measure_excluded_geographical_area.geographical_area_sid = row[2]

            self.measure_excluded_geographical_areas.append(measure_excluded_geographical_area)
        self.end_timer("Getting measure excluded geographical areas")

    def get_footnote_association_measures(self, iteration):
        # Get measure footnotes
        self.start_timer("Getting measure footnotes")
        self.footnote_association_measures = []
        sql = """
        select m.measure_sid, fam.footnote_type_id, fam.footnote_id
        from footnote_association_measures fam, utils.materialized_measures_real_end_dates m
        where m.measure_sid = fam.measure_sid
        and left(m.goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by m.goods_nomenclature_item_id, m.measure_sid, fam.footnote_id, fam.footnote_id ;
        """
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            footnote_association_measure = FootnoteAssociationMeasure()
            footnote_association_measure.measure_sid = row[0]
            footnote_association_measure.footnote_type_id = row[1]
            footnote_association_measure.footnote_id = row[2]

            self.footnote_association_measures.append(footnote_association_measure)
        self.end_timer("Getting measure footnotes")

    def get_measures(self, iteration):
        # Get measures
        self.start_timer("Getting measures")
        self.measures = []

        # Sort by measure SID to speed up processing in the assignment functions later
        sql = """select m.*, mt.measure_type_series_id,
        mt.measure_component_applicable_code, mt.trade_movement_code
        from utils.materialized_measures_real_end_dates m, measure_types mt
        where m.measure_type_id = mt.measure_type_id
        and left(goods_nomenclature_item_id, """ + str(len(str(iteration))) + """) = '""" + str(iteration) + """'
        and (m.validity_end_date is null or m.validity_end_date >= '""" + self.SNAPSHOT_DATE + """')
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        order by measure_sid;"""

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
            measure.additional_code_sid = row[16]
            measure.validity_start_date = row[18]
            measure.validity_end_date = row[19]
            measure.operation_date = row[20]
            measure.measure_type_series_id = row[21]
            measure.measure_component_applicable_code = int(row[22])
            measure.trade_movement_code = row[23]
            measure.get_import_export()
            measure.expand_raw_data(self.measure_types, self.geographical_areas)

            self.measures.append(measure)

        self.end_timer("Getting measures")

    def get_all_footnotes(self):
        self.start_timer("Getting and writing all footnotes for CSV export")
        self.measures = []
        sql = """
        with footnotes_cte as (
        SELECT fd1.footnote_type_id,
        fd1.footnote_id,
        fd1.footnote_type_id || fd1.footnote_id as code,
        fd1.description,
        f1.validity_start_date,
        f1.validity_end_date
        FROM footnote_descriptions fd1,
        footnotes f1
        WHERE fd1.footnote_id = f1.footnote_id
        AND fd1.footnote_type_id = f1.footnote_type_id
        AND (fd1.footnote_description_period_sid IN ( SELECT max(ft2.footnote_description_period_sid) AS max
        FROM footnote_descriptions ft2
        WHERE fd1.footnote_type_id = ft2.footnote_type_id AND fd1.footnote_id = ft2.footnote_id))
        )
        select distinct f.code, f.description, f.validity_start_date, f.validity_end_date, 'measure' as footnote_class
        from footnotes_cte f, footnote_association_measures fam, utils.materialized_measures_real_end_dates m
        where f.footnote_id = fam.footnote_id
        and f.footnote_type_id = fam.footnote_type_id
        and fam.measure_sid = m.measure_sid
        and (m.validity_end_date is null or m.validity_end_date >= %s)
        and m.validity_start_date <= %s
        and f.validity_end_date is null

        union

        select distinct f.code, f.description, f.validity_start_date, f.validity_end_date, 'commodity' as footnote_class
        from footnotes_cte f, footnote_association_goods_nomenclatures fagn, goods_nomenclatures gn
        where f.footnote_id = fagn.footnote_id
        and f.footnote_type_id = fagn.footnote_type
        and fagn.goods_nomenclature_sid = gn.goods_nomenclature_sid
        and (gn.validity_end_date is null or gn.validity_end_date >= %s)
        and gn.validity_start_date <= %s
        and f.validity_end_date is null
        order by 1;
        """

        d = Database()
        params = [
            self.SNAPSHOT_DATE,
            self.SNAPSHOT_DATE,
            self.SNAPSHOT_DATE,
            self.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
        self.all_footnotes = []
        for row in rows:
            footnote = Footnote()
            footnote.code = row[0]
            footnote.description = row[1]
            footnote.validity_start_date = row[2]
            footnote.validity_end_date = row[3]
            footnote.footnote_class = row[4]
            footnote.get_footnote_csv_string()

            self.all_footnotes.append(footnote)
            self.footnote_csv_file.write(footnote.footnote_csv_string)

        self.footnote_csv_file.close()
        self.end_timer("Getting and writing all footnotes for CSV export")

    def get_all_certificates(self):
        self.start_timer("Getting and writing all certificates for CSV export")
        self.measures = []
        sql = """
        with certificate_cte as (
        SELECT cd1.certificate_type_code,
        cd1.certificate_code,
        cd1.certificate_type_code || cd1.certificate_code AS code,
        cd1.description,
        c.validity_start_date,
        c.validity_end_date
        FROM certificate_descriptions cd1,
        certificates c
        WHERE c.certificate_code = cd1.certificate_code AND c.certificate_type_code = cd1.certificate_type_code AND (cd1.oid IN ( SELECT max(cd2.oid) AS max
        FROM certificate_descriptions cd2
        WHERE cd1.certificate_type_code = cd2.certificate_type_code AND cd1.certificate_code = cd2.certificate_code))
        )
        select distinct c.code, c.description, c.validity_start_date, c.validity_end_date
        from measure_conditions mc, utils.materialized_measures_real_end_dates m, certificate_cte c
        where m.measure_sid = mc.measure_sid
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and mc.certificate_type_code = c.certificate_type_code
        and mc.certificate_code = c.certificate_code
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        and (c.validity_end_date is null or c.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        order by 1
        """
        d = Database()
        rows = d.run_query(sql)
        self.all_certificates = []
        for row in rows:
            certificate = Certificate()
            certificate.code = row[0]
            certificate.description = row[1]
            certificate.validity_start_date = row[2]
            certificate.validity_end_date = row[3]
            certificate.get_csv_string()

            self.all_certificates.append(certificate)
            self.certificate_csv_file.write(certificate.certificate_csv_string)

        self.end_timer("Getting and writing all certificates for CSV export")
        self.certificate_csv_file.close()

    def get_all_geographies(self):
        self.start_timer("Getting and writing all geographical areas for CSV export")
        self.measures = []
        sql = """
        with cte_geography as (
            SELECT g.geographical_area_sid,
            geo1.geographical_area_id,
            geo1.description,
            case
            when geographical_code = '0' then 'Country'
            when geographical_code = '1' then 'Country group'
            when geographical_code = '2' then 'Region'
            end as area_type
            FROM geographical_area_descriptions geo1,
            geographical_areas g
            WHERE g.geographical_area_id::text = geo1.geographical_area_id::text AND (geo1.geographical_area_description_period_sid IN ( SELECT max(geo2.geographical_area_description_period_sid) AS max
            FROM geographical_area_descriptions geo2
            WHERE geo1.geographical_area_id::text = geo2.geographical_area_id::text))
            and g.validity_end_date is null
        ), cte_members as (
            SELECT ga1.geographical_area_sid AS parent_sid,
            ga1.geographical_area_id AS parent_id,
            ga2.geographical_area_sid AS child_sid,
            ga2.geographical_area_id AS child_id
            FROM geographical_area_memberships gam,
            geographical_areas ga1,
            geographical_areas ga2
            WHERE ga1.geographical_area_sid = gam.geographical_area_group_sid
            AND ga2.geographical_area_sid = gam.geographical_area_sid
            and gam.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
            and (gam.validity_end_date is null or gam.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        )
        select g.geographical_area_id, g.description, g.area_type,
        string_agg(distinct g2.child_id, '|' order by g2.child_id) as members
        from cte_geography g
        left outer join cte_members g2 on g.geographical_area_sid = g2.parent_sid
        group by g.geographical_area_id, g.description, g.area_type
        order by 1;
        """
        d = Database()
        rows = d.run_query(sql)
        self.all_geographies = []
        for row in rows:
            geographical_area = GeographicalArea2()
            geographical_area.geographical_area_id = row[0]
            geographical_area.description = row[1]
            geographical_area.area_type = row[2]
            geographical_area.members = row[3]
            geographical_area.get_csv_string()

            self.all_geographies.append(geographical_area)
            self.geography_csv_file.write(geographical_area.csv_string)

        self.end_timer("Getting and writing all geographical areas for CSV export")
        self.geography_csv_file.close()

    def get_all_measure_types(self):
        self.start_timer("Getting and writing all measure types for CSV export")
        sql = """
        select mtd.measure_type_id, mtd.description, count(m.*)
        from measure_types mt, measure_type_descriptions mtd, utils.materialized_measures_real_end_dates m
        where mt.measure_type_id = mtd.measure_type_id
        and m.measure_type_id = mt.measure_type_id
        and m.validity_end_date is null
        group by mtd.measure_type_id, mtd.description
        order by measure_type_id
        """
        d = Database()
        rows = d.run_query(sql)
        self.all_measure_types = []
        for row in rows:
            measure_type = MeasureType2()
            measure_type.measure_type_id = row[0]
            measure_type.description = row[1]
            measure_type.get_csv_string()

            self.all_measure_types.append(measure_type)
            self.measure_type_csv_file.write(measure_type.csv_string)

        self.end_timer("Getting and writing all measure types for CSV export")
        self.measure_type_csv_file.close()

    def get_all_additional_codes(self):
        self.start_timer("Getting and writing all additional codes for CSV export")
        sql = """
        select distinct ac.code, ac.description, ac.validity_start_date, ac.validity_end_date, acd.description as additional_code_description
        from utils.additional_codes ac, utils.materialized_measures_real_end_dates m, additional_code_type_descriptions acd
        where ac.additional_code_type_id = m.additional_code_type_id
        and ac.additional_code = m.additional_code_id
        and (m.validity_end_date is null or m.validity_end_date::date > current_date)
        and ac.additional_code_type_id = acd.additional_code_type_id
        order by 1;
        """
        d = Database()
        rows = d.run_query(sql)
        self.all_additional_codes = []
        for row in rows:
            additional_code = AdditionalCode()
            additional_code.code = row[0]
            additional_code.description = f.strip_quotes(row[1])
            additional_code.validity_start_date = f.format_date(row[2], "%Y-%m-%d")
            additional_code.validity_end_date = f.format_date(row[3], "%Y-%m-%d")
            additional_code.additional_code_type_description = f.strip_quotes(row[4])

            additional_code.get_csv_string()

            self.all_additional_codes.append(additional_code)
            self.additional_code_csv_file.write(additional_code.csv_string)

        self.end_timer("Getting and writing all additional codes for CSV export")
        self.additional_code_csv_file.close()

    def get_all_quotas(self):
        self.start_timer("Getting and writing all quota definitions for CSV export")
        self.quota_commodities = []
        sql = """
        select ordernumber, string_agg(distinct goods_nomenclature_item_id, '|' order by m.goods_nomenclature_item_id)
        from utils.materialized_measures_real_end_dates m
        where ordernumber like '05%'
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        group by ordernumber
        order by ordernumber
        """
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            quota_commodity = QuotaCommodity()
            quota_commodity.quota_order_number_id = row[0]
            quota_commodity.commodities = row[1]

            self.quota_commodities.append(quota_commodity)

        # Get quota exclusions
        self.quota_exclusions = []
        sql = """
        select qon.quota_order_number_id, qon.quota_order_number_sid,
        string_agg(ga.geographical_area_id, '|' order by ga.geographical_area_id) as exclusions
        from quota_order_number_origin_exclusions qonoe, quota_order_number_origins qono,
        quota_order_numbers qon, geographical_areas ga
        where qono.quota_order_number_origin_sid = qonoe.quota_order_number_origin_sid
        and qon.quota_order_number_sid = qono.quota_order_number_sid
        and ga.geographical_area_sid = qonoe.excluded_geographical_area_sid
        and qon.quota_order_number_id like '05%'
        group by qon.quota_order_number_id, qon.quota_order_number_sid
        order by 1;"""
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            quota_exclusion = QuotaExclusion()
            quota_exclusion.quota_order_number_id = row[0]
            quota_exclusion.quota_order_number_sid = row[1]
            quota_exclusion.exclusions = row[2]

            self.quota_exclusions.append(quota_exclusion)

        # Get quota definitions
        self.all_quota_definitions = []

        sql = """
        select qon.quota_order_number_sid, qon.quota_order_number_id, qd.validity_start_date::text, qd.validity_end_date::text,
        qd.initial_volume,
        qd.measurement_unit_code || ' ' || coalesce(qd.measurement_unit_qualifier_code, '') as unit,
        qd.critical_state, qd.critical_threshold, 'First Come First Served' as quota_type,
        string_agg(distinct qono.geographical_area_id, '|' order by qono.geographical_area_id) as origins
        from quota_order_numbers qon, quota_definitions qd, quota_order_number_origins qono
        where qd.quota_order_number_sid = qon.quota_order_number_sid
        and qon.quota_order_number_sid = qono.quota_order_number_sid
        and qon.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (qon.validity_end_date is null or qon.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        and qd.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (qd.validity_end_date is null or qd.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        and qon.quota_order_number_id like '05%'
        group by qon.quota_order_number_sid, qon.quota_order_number_id, qd.validity_start_date, qd.validity_end_date,
        qd.initial_volume, qd.measurement_unit_code, qd.measurement_unit_qualifier_code,
        qd.critical_state, qd.critical_threshold

        union

        select Null as quota_order_number_sid, m.ordernumber as quota_order_number_id,
        m.validity_start_date::text, m.validity_end_date, Null as initial_volume,
        Null as unit, Null as critical_state, Null as critical_threshold, 'Licensed' as quota_type,
        string_agg(distinct m.geographical_area_id, '|' order by m.geographical_area_id) as origins
        from utils.materialized_measures_real_end_dates m
        where ordernumber like '054%'
        and m.validity_start_date <= '""" + self.SNAPSHOT_DATE + """'
        and (m.validity_end_date is null or m.validity_end_date > '""" + self.SNAPSHOT_DATE + """')
        group by m.ordernumber, m.validity_start_date, m.validity_end_date

        order by 2
        """

        d = Database()
        rows = d.run_query(sql)
        self.all_quota_definitions = []
        for row in rows:
            quota_definition = QuotaDefinition()
            quota_definition.quota_order_number_sid = row[0]
            quota_definition.quota_order_number_id = row[1]
            quota_definition.validity_start_date = row[2]
            quota_definition.validity_end_date = row[3]
            quota_definition.initial_volume = row[4]
            quota_definition.unit = row[5]
            quota_definition.critical_state = row[6]
            quota_definition.critical_threshold = row[7]
            quota_definition.quota_type = row[8]
            quota_definition.origins = row[9]
            # Assign the exclusions to the definitions
            for exclusion in self.quota_exclusions:
                if exclusion.quota_order_number_sid == quota_definition.quota_order_number_sid:
                    quota_definition.exclusions = exclusion.exclusions
                    break

            # Assign the commodities to the definitions
            for quota_commodity in self.quota_commodities:
                if quota_commodity.quota_order_number_id == quota_definition.quota_order_number_id:
                    quota_definition.commodities = quota_commodity.commodities
                    break

            quota_definition.get_csv_string()

            self.all_quota_definitions.append(quota_definition)

        for quota_definition in self.all_quota_definitions:
            if quota_definition.commodities != "":
                self.quota_csv_file.write(quota_definition.csv_string)

        self.end_timer("Getting and writing all quota definitions for CSV export")
        self.quota_csv_file.close()

    def rebase_chapters(self):
        # Reset the indent of chapters to -1, so that they are
        # omitted from the hierarchy string
        self.start_timer("Rebasing chapters")
        for commodity in self.commodities:
            commodity.get_entity_type()

            # Do not rebase data for the CSV file
            commodity.number_indents_csv = commodity.number_indents

            # Rebase data for working out hierarchical inheritance
            if commodity.significant_digits == 2:
                commodity.number_indents = -1

        self.end_timer("Rebasing chapters")

    def build_commodity_hierarchy(self):
        # Builds the commodity hierarchy
        self.rebase_chapters()
        self.start_timer("Building commodity hierarchy")
        commodity_count = len(self.commodities)
        for loop in range(0, commodity_count):
            commodity = self.commodities[loop]
            current_indent = commodity.number_indents
            for loop2 in range(loop - 1, -1, -1):
                commodity2 = self.commodities[loop2]
                if commodity2.number_indents < current_indent:
                    if commodity.leaf == 1:
                        if commodity.significant_digits == 10:
                            if commodity2.number_indents == commodity.number_indents - 1:
                                if commodity2.significant_digits in (4, 6):
                                    commodity2.pseudo_line = True

                    commodity.hierarchy.append(commodity2)
                    current_indent = commodity2.number_indents
                if commodity2.number_indents == -1:
                    break
            commodity.hierarchy.reverse()
            commodity.build_hierarchy_string()
            commodity.build_csv_hierarchy_string()
        self.end_timer("Building commodity hierarchy")

    def write_commodities(self):
        # Write all commodities
        self.start_timer("Writing commodities")
        barred_series = ['E', 'F', 'G', 'H', 'K', 'L', 'M', "N", "O", "R", "S", "Z"]
        for commodity in self.commodities:
            commodity_string = ""
            commodity_string += str(commodity.goods_nomenclature_sid) + ","
            commodity_string += CommonString.quote_char + commodity.COMMODITY_CODE + CommonString.quote_char + ","
            commodity_string += CommonString.quote_char + commodity.productline_suffix + CommonString.quote_char + ","
            commodity_string += commodity.validity_start_date.strftime(
                '%Y-%m-%d') + ","
            if commodity.validity_end_date is None:
                commodity_string += ","
            else:
                commodity_string += commodity.validity_end_date.strftime('%Y-%m-%d') + ","
            commodity_string += CommonString.quote_char + commodity.description_csv + CommonString.quote_char + ","
            commodity_string += str(commodity.number_indents_csv) + ","
            commodity_string += CommonString.quote_char + commodity.entity_type + CommonString.quote_char + ","
            commodity_string += CommonString.quote_char + f.YN(commodity.leaf) + CommonString.quote_char + ","
            commodity_string += CommonString.quote_char + commodity.COMMODITY_CODE + "-" + commodity.productline_suffix + CommonString.quote_char + ","
            commodity_string += CommonString.quote_char + commodity.hierarchy_sid_string + CommonString.quote_char + ","
            commodity_string += CommonString.quote_char + commodity.hierarchy_id_string + CommonString.quote_char

            self.commodity_csv_file.write(commodity_string + CommonString.line_feed)

            # Write measures for the ICL VME file
            if commodity.leaf == 1 or (commodity.significant_digits >= 8 and commodity.productline_suffix == "80") or commodity.pseudo_line is True:
                self.commodity_count += 1
                self.icl_vme_file.write(commodity.extract_line)
                if self.WRITE_ADDITIONAL_CODES == 1:
                    if commodity.additional_code_string != "":
                        self.additional_code_count += 1
                        self.icl_vme_file.write(commodity.additional_code_string)

                if self.WRITE_MEASURES == 1:
                    for measure in commodity.measures_inherited:
                        if measure.measure_type_series_id not in barred_series:
                            if measure.RECORD_TYPE == "MX":
                                self.measure_exception_count += 1
                            else:
                                self.measure_count += measure.line_count

                            # Write to the ICL VME file
                            # Only write measures of type CVD and ADD once, not multiple times
                            skip_write = False

                            if measure.MEASURE_TYPE_CODE == "ADD":
                                if measure.geographical_area_id in commodity.written_ADD:
                                    skip_write = True

                            if measure.MEASURE_TYPE_CODE == "CVD":
                                if measure.geographical_area_id in commodity.written_CVD:
                                    skip_write = True

                            if measure.MEASURE_TYPE_CODE == "ADP":
                                if measure.geographical_area_id in commodity.written_ADP:
                                    skip_write = True

                            if measure.MEASURE_TYPE_CODE == "CVP":
                                if measure.geographical_area_id in commodity.written_CVP:
                                    skip_write = True

                            if not skip_write:
                                self.icl_vme_file.write(measure.extract_line)

                            # Prevent ADD and CVD measure types etc. from being written again
                            if measure.MEASURE_TYPE_CODE == "ADD":
                                commodity.written_ADD.append(measure.geographical_area_id)

                            if measure.MEASURE_TYPE_CODE == "CVD":
                                commodity.written_CVD.append(measure.geographical_area_id)

                            if measure.MEASURE_TYPE_CODE == "ADP":
                                commodity.written_ADP.append(measure.geographical_area_id)

                            if measure.MEASURE_TYPE_CODE == "CVP":
                                commodity.written_CVP.append(measure.geographical_area_id)

                    self.pipe_pr_measures_into_icl_vme_file(commodity.COMMODITY_CODE)

            # Write measures to the measures CSV file
            if commodity.leaf == 1:
                measure_sids = []
                for measure in commodity.measures_inherited:
                    if measure.extract_line_csv != "":
                        if measure.measure_sid not in measure_sids:
                            s = measure.extract_line_csv
                            s = s.replace("COMMODITY_SID_PLACEHOLDER", str(commodity.goods_nomenclature_sid))
                            s = s.replace("COMMODITY_CODE_PLACEHOLDER", commodity.COMMODITY_CODE)
                            self.measure_csv_file.write(s)

                            if measure.measure_type_id in ("103", "105"):
                                s = measure.extract_line_mfn_csv
                                s = s.replace("COMMODITY_SID_PLACEHOLDER", str(commodity.goods_nomenclature_sid))
                                s = s.replace("COMMODITY_CODE_PLACEHOLDER", commodity.COMMODITY_CODE)
                                s = s.replace("COMMODITY_CODE_DESCRIPTION", self.commodities_dict[commodity.COMMODITY_CODE])

                                self.mfn_csv_file.write(s)

                    measure_sids.append(measure.measure_sid)

        self.end_timer("Writing commodities")

    def pipe_pr_measures_into_icl_vme_file(self, commodity):
        has_found = False
        for pr_measure in self.pr_measures:
            if pr_measure.commodity == commodity:
                self.measure_count += 1
                self.icl_vme_file.write(pr_measure.line + CommonString.line_feed)
                has_found = True
            else:
                if has_found is True:
                    break

    def get_folders(self):
        self.current_folder = os.getcwd()
        self.data_folder = os.path.join(self.current_folder, "data")
        self.reference_folder = os.path.join(self.data_folder, "reference")
        self.data_in_folder = os.path.join(self.data_folder, "in")
        self.data_out_folder = os.path.join(self.data_folder, "out")
        self.export_folder = os.path.join(self.current_folder, "_export")
        self.documentation_folder = os.path.join(self.current_folder, "documentation")
        self.documentation_file = os.path.join(self.documentation_folder, "Documentation on tariff CSV data files.docx")
        self.correlation_file = os.path.join(self.documentation_folder, "Ascii file and CDS measure type correlation table 1.0.docx")

        # Make the date-specific folder
        date_time_obj = datetime.strptime(self.SNAPSHOT_DATE, '%Y-%m-%d')
        self.year = date_time_obj.strftime("%Y")
        self.month = date_time_obj.strftime("%b").lower()
        self.month2 = date_time_obj.strftime("%m").lower()
        self.day = date_time_obj.strftime("%d")

        date_folder = self.year + "-" + self.month2 + "-" + self.day
        self.dated_folder = os.path.join(self.export_folder, date_folder)
        os.makedirs(self.dated_folder, exist_ok=True)

        # Under the date-specific folder, also make a scope (UK/XI) folder
        self.scope_folder = os.path.join(self.dated_folder, self.scope)
        os.makedirs(self.scope_folder, exist_ok=True)

        # Finally, make the destination folders
        self.icl_vme_folder = os.path.join(self.scope_folder, "icl_vme")
        self.csv_folder = os.path.join(self.scope_folder, "csv")
        self.delta_folder = os.path.join(self.scope_folder, "delta")
        self.log_folder = os.path.join(self.scope_folder, "logs")
        self.log_filename = os.path.join(self.log_folder, "etf_creation_log.txt")

        os.makedirs(self.icl_vme_folder, exist_ok=True)
        os.makedirs(self.csv_folder, exist_ok=True)
        os.makedirs(self.delta_folder, exist_ok=True)
        os.makedirs(self.log_folder, exist_ok=True)

    def open_extract(self):
        if CommonString.divider == "|":
            self.filename = "hmrc-tariff-ascii-" + self.SNAPSHOT_DATE + "-piped.txt"
        else:
            self.filename = "hmrc-tariff-ascii-" + self.SNAPSHOT_DATE + ".txt"

        # Work out the path to the ICL VME extract
        self.filepath_icl_vme = os.path.join(self.icl_vme_folder, self.filename)
        self.icl_vme_file = open(self.filepath_icl_vme, "w+")

        # Measures CSV extract filename
        self.measure_csv_filename = self.filename.replace(".txt", ".csv")
        self.measure_csv_filename = self.measure_csv_filename.replace("ascii", "measures")
        self.measure_csv_filepath = os.path.join(self.csv_folder, self.measure_csv_filename)
        self.measure_csv_file = open(self.measure_csv_filepath, "w+")
        self.measure_csv_file.write('"commodity__sid","commodity__code","measure__sid","measure__type__id","measure__type__description","measure__additional_code__code","measure__additional_code__description","measure__duty_expression","measure__effective_start_date","measure__effective_end_date","measure__reduction_indicator","measure__footnotes","measure__conditions","measure__geographical_area__sid","measure__geographical_area__id","measure__geographical_area__description","measure__excluded_geographical_areas__ids","measure__excluded_geographical_areas__descriptions","measure__quota__order_number"' + CommonString.line_feed)

        # MFN (103 / 105) CSV extract filename
        self.mfn_csv_filename = self.filename.replace(".txt", ".csv")
        self.mfn_csv_filename = self.mfn_csv_filename.replace("ascii", "mfn")
        self.mfn_csv_filepath = os.path.join(self.csv_folder, self.mfn_csv_filename)
        self.mfn_csv_file = open(self.mfn_csv_filepath, "w+")
        self.mfn_csv_file.write('"commodity__sid","commodity__code","commodity__code__description","measure__sid","measure__type__id","measure__type__description","measure__additional_code__code","measure__additional_code__description","measure__duty_expression","measure__effective_start_date","measure__effective_end_date"' + CommonString.line_feed)

        # Commodities CSV extract filename
        self.commodity_csv_filename = self.measure_csv_filename.replace("measures", "commodities")
        self.commodity_csv_filepath = os.path.join(self.csv_folder, self.commodity_csv_filename)
        self.commodity_csv_file = open(self.commodity_csv_filepath, "w+")
        self.commodity_csv_file.write('"commodity__sid","commodity__code","productline__suffix","start__date","end__date","description","indents","entity__type","end__line","commodity__code__pls","hierarchy__of__sids","hierarchy__of__ids"' + CommonString.line_feed)

        if self.WRITE_ANCILLARY_FILES:
            # Footnotes CSV extract filename
            self.footnote_csv_filename = self.measure_csv_filename.replace("measures", "footnotes")
            self.footnote_csv_filepath = os.path.join(self.csv_folder, self.footnote_csv_filename)
            self.footnote_csv_file = open(self.footnote_csv_filepath, "w+")
            self.footnote_csv_file.write('"footnote__id","footnote__description","start__date","end__date","footnote__type"' + CommonString.line_feed)

            # Certificates CSV extract filename
            self.certificate_csv_filename = self.measure_csv_filename.replace("measures", "certificates")
            self.certificate_csv_filepath = os.path.join(self.csv_folder, self.certificate_csv_filename)
            self.certificate_csv_file = open(self.certificate_csv_filepath, "w+")
            self.certificate_csv_file.write('"certificate__id","certificate__description","start__date","end__date"' + CommonString.line_feed)

            # Quotas CSV extract filename
            self.quota_csv_filename = self.measure_csv_filename.replace("measures", "quotas")
            self.quota_csv_filepath = os.path.join(self.csv_folder, self.quota_csv_filename)
            self.quota_csv_file = open(self.quota_csv_filepath, "w+")
            self.quota_csv_file.write(
                '"quota__order__number__id","definition__start__date","definition__end__date","initial__volume","unit","critical__state","critical__threshold","quota__type","origins","origin__exclusions","commodities"' + CommonString.line_feed)

            # Geography CSV extract filename
            self.geography_csv_filename = self.measure_csv_filename.replace("measures", "geography")
            self.geography_csv_filepath = os.path.join(self.csv_folder, self.geography_csv_filename)
            self.geography_csv_file = open(self.geography_csv_filepath, "w+")
            self.geography_csv_file.write('"geographical_area_id","description","area_type","members"' + CommonString.line_feed)

            # Measure type CSV extract filename
            self.measure_type_csv_filename = self.measure_csv_filename.replace("measures", "measure_type")
            self.measure_type_csv_filepath = os.path.join(self.csv_folder, self.measure_type_csv_filename)
            self.measure_type_csv_file = open(self.measure_type_csv_filepath, "w+")
            self.measure_type_csv_file.write('"measure_type_id","description"' + CommonString.line_feed)

            # Additional code CSV extract filename
            self.additional_code_csv_filename = self.measure_csv_filename.replace("measures", "additional_code")
            self.additional_code_csv_filepath = os.path.join(self.csv_folder, self.additional_code_csv_filename)
            self.additional_code_csv_file = open(self.additional_code_csv_filepath, "w+")
            self.additional_code_csv_file.write('"additional code","description","start date","end date","type description"' + CommonString.line_feed)

    def close_extract(self):
        self.icl_vme_file.close()
        self.measure_csv_file.close()
        self.mfn_csv_file.close()
        self.commodity_csv_file.close()

        if self.WRITE_ANCILLARY_FILES == 1:
            self.footnote_csv_file.close()
            self.certificate_csv_file.close()
            self.quota_csv_file.close()
            self.geography_csv_file.close()
            self.measure_type_csv_file.close()
            self.additional_code_csv_file.close()

    def create_email_message(self):
        self.send_mail = int(os.getenv('SEND_MAIL'))
        if self.send_mail == 0:
            return

        self.html_content = """
        <p style="color:#000">Dear all,</p>
        <p style="color:#000">The following data files are available for download, representing tariff data for <b>{0}</b>:</p>
        <p style="color:#000">Changes in this issue are as listed in the relevant links, as follows:</p>

        <table cellspacing="0">
            <tr>
                <th style="text-align:left;padding:3px 0px">Description</th>
                <th style="text-align:left;padding:3px 3px">File</th>
            </tr>
            <tr>
                <td style="padding:3px 0px">Commodity changes</td>
                <td style="padding:3px 3px">{1}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Measure changes</td>
                <td style="padding:3px 3px">{2}</td>
            </tr>
        </table>

        <p style="color:#000">Two additional files are attached to this email, as follows:</p>
        <ul>
            <li>Documentation on the attached CSV formats</li>
            <li>ASCII file and CDS measure type correlation table</li>
        </ul>

        <p style="color:#000"><b>Files compressed using ZIP compression</b>:</p>
        <table cellspacing="0">
            <tr>
                <th style="text-align:left;padding:3px 0px">Description</th>
                <th style="text-align:left;padding:3px 3px">File</th>
            </tr>
            <tr>
                <td style="padding:3px 0px">Electronic Tariff File (ICL VME format)</td>
                <td style="padding:3px 3px">{3}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Measures, as applied to commodity codes (CSV)</td>
                <td style="padding:3px 3px">{4}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Commodities</td>
                <td style="padding:3px 3px">{5}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Footnotes</td>
                <td style="padding:3px 3px">{6}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Certificates</td>
                <td style="padding:3px 3px">{7}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Quotas</td>
                <td style="padding:3px 3px">{8}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Geographical areas</td>
                <td style="padding:3px 3px">{9}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Measure types</td>
                <td style="padding:3px 3px">{10}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Additional codes</td>
                <td style="padding:3px 3px">{11}</td>
            </tr>
        </table>

        <br><br><p style="color:#000"><b>Files compressed using 7z compression</b>:</p>
        <table cellspacing="0">
            <tr>
                <th style="text-align:left;padding:3px 0px">Description</th>
                <th style="text-align:left;padding:3px 3px">File</th>
            </tr>
            <tr>
                <td style="padding:3px 0px">Electronic Tariff File (ICL VME format)</td>
                <td style="padding:3px 3px">{12}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Measures, as applied to commodity codes (CSV)</td>
                <td style="padding:3px 3px">{13}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Commodities</td>
                <td style="padding:3px 3px">{14}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Footnotes</td>
                <td style="padding:3px 3px">{15}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Certificates</td>
                <td style="padding:3px 3px">{16}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Quotas</td>
                <td style="padding:3px 3px">{17}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Geographical areas</td>
                <td style="padding:3px 3px">{18}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Measure types</td>
                <td style="padding:3px 3px">{19}</td>
            </tr>
            <tr>
                <td style="padding:3px 0px">Additional codes</td>
                <td style="padding:3px 3px">{20}</td>
            </tr>
        </table>

        <p style="color:#000">Thank you,</p>
        <p style="color:#000">The Online Tariff Team.</p>""".format(
            self.SNAPSHOT_DATE,
            self.bucket_url + self.aws_path_commodities_delta_tuple[1],
            self.bucket_url + self.aws_path_measures_delta_tuple[1],
            self.bucket_url + self.aws_path_icl_vme_tuple[1],
            self.bucket_url + self.aws_path_measures_csv_tuple[1],
            self.bucket_url + self.aws_path_commodities_csv_tuple[1],
            self.bucket_url + self.aws_path_footnotes_csv_tuple[1],
            self.bucket_url + self.aws_path_certificates_csv_tuple[1],
            self.bucket_url + self.aws_path_quotas_csv_tuple[1],
            self.bucket_url + self.aws_path_geographical_areas_csv_tuple[1],
            self.bucket_url + self.aws_path_measure_types_csv_tuple[1],
            self.bucket_url + self.aws_path_additional_codes_csv_tuple[1],
            self.bucket_url + self.aws_path_icl_vme_tuple[0],
            self.bucket_url + self.aws_path_measures_csv_tuple[0],
            self.bucket_url + self.aws_path_commodities_csv_tuple[0],
            self.bucket_url + self.aws_path_footnotes_csv_tuple[0],
            self.bucket_url + self.aws_path_certificates_csv_tuple[0],
            self.bucket_url + self.aws_path_quotas_csv_tuple[0],
            self.bucket_url + self.aws_path_geographical_areas_csv_tuple[0],
            self.bucket_url + self.aws_path_measure_types_csv_tuple[0],
            self.bucket_url + self.aws_path_additional_codes_csv_tuple[0]
        )

    def send_email_message(self):
        self.send_mail = int(os.getenv('SEND_MAIL'))
        if self.send_mail == 0:
            return
        subject = "Issue of updated HMRC Electronic Tariff File for " + self.SNAPSHOT_DATE
        attachment_list = [
            self.documentation_file,
            self.correlation_file
        ]
        s = SendgridMailer(subject, self.html_content, attachment_list)  # self.documentation_file)
        s.send()

    def zip_and_upload(self):
        self.aws_path_icl_vme_tuple = Zipper(self.filepath_icl_vme, self.scope, "icl_vme", "ICL VME file").compress()
        self.aws_path_measures_csv_tuple = Zipper(self.measure_csv_filepath, self.scope, "csv", "Measures CSV").compress()
        self.aws_path_mfn_csv_tuple = Zipper(self.mfn_csv_filepath, self.scope, "csv", "Third country duty CSV").compress()
        self.aws_path_commodities_csv_tuple = Zipper(self.commodity_csv_filepath, self.scope, "csv", "Commodities CSV").compress()
        if self.WRITE_ANCILLARY_FILES:
            self.aws_path_footnotes_csv_tuple = Zipper(self.footnote_csv_filepath, self.scope, "csv", "Footnotes CSV").compress()
            self.aws_path_certificates_csv_tuple = Zipper(self.certificate_csv_filepath, self.scope, "csv", "Certificates CSV").compress()
            self.aws_path_quotas_csv_tuple = Zipper(self.quota_csv_filepath, self.scope, "csv", "Quotas CSV").compress()
            self.aws_path_geographical_areas_csv_tuple = Zipper(self.geography_csv_filepath, self.scope, "csv", "Geographical areas CSV").compress()
            self.aws_path_measure_types_csv_tuple = Zipper(self.measure_type_csv_filepath, self.scope, "csv", "Geographical areas CSV").compress()
            self.aws_path_additional_codes_csv_tuple = Zipper(self.additional_code_csv_filepath, self.scope, "csv", "Additional codes CSV").compress()
        else:
            self.aws_path_footnotes_csv_tuple = ("n/a", "n/a")
            self.aws_path_certificates_csv_tuple = ("n/a", "n/a")
            self.aws_path_quotas_csv_tuple = ("n/a", "n/a")
            self.aws_path_geographical_areas_csv_tuple = ("n/a", "n/a")
            self.aws_path_measure_types_csv_tuple = ("n/a", "n/a")
            self.aws_path_additional_codes_csv_tuple = ("n/a", "n/a")

        # Delta description files
        self.aws_path_commodities_delta_tuple = Zipper(self.delta.commodities_filename, self.scope, "delta", "Changes to commodity codes").compress()
        self.aws_path_measures_delta_tuple = Zipper(self.delta.measures_filename, self.scope, "delta", "Changes to measures").compress()

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
            self.commodities_with_footnotes.append(
                footnote.goods_nomenclature_sid)

        self.commodities_with_footnotes = set(self.commodities_with_footnotes)

    def assign_commodity_footnotes(self):
        self.start_timer("Assigning footnotes to commodities")
        for footnote_association in self.commodity_footnotes:
            for commodity in self.commodities:
                if footnote_association.goods_nomenclature_sid == commodity.goods_nomenclature_sid:
                    commodity.footnotes.append(footnote_association)
                    break

        for commodity in self.commodities:
            commodity.append_footnotes_to_description()

        self.end_timer("Assigning footnotes to commodities")

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
        self.icl_vme_file.write(self.footnote_header)

    def write_footnote_footer(self):
        # CF0000120
        # RECORD-TYPE 2
        # FOOTNOTE-RECORD-COUNT 7
        self.footnote_footer = "CF"
        self.footnote_footer += str(len(self.footnotes)).zfill(7)
        self.icl_vme_file.write(self.footnote_footer)

    def write_commodity_header(self):
        # HF2020121500000021001
        # RECORD-TYPE 2
        # DATE-CREATED 8
        # TIME-CREATED 6
        # RUN-NUMBER 5

        my_date = date.today()
        year, week_num, day_of_week = my_date.isocalendar()
        week_num = str(week_num).zfill(3)
        year = datetime.strftime(my_date, "%y")

        self.commodity_header = "HE"
        self.commodity_header += self.YYYYMMDD(datetime.now())
        self.commodity_header += self.HHMMSS(datetime.now())
        self.commodity_header += year
        self.commodity_header += week_num
        self.commodity_header += CommonString.line_feed
        self.icl_vme_file.write(self.commodity_header)

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

        # self.measure_exception_count = 0
        total_record_count = self.commodity_count + self.additional_code_count + \
            self.measure_count + self.measure_exception_count

        self.CM_RECORD_COUNT = str(self.commodity_count).rjust(7, "0")
        self.CA_RECORD_COUNT = str(self.additional_code_count).rjust(7, "0")
        ME_RECORD_COUNT = str(self.measure_count).rjust(7, "0")
        self.MD_RECORD_COUNT = "0000000"
        self.MX_RECORD_COUNT = str(self.measure_exception_count).rjust(7, "0")
        self.TOTAL_RECORD_COUNT = str(total_record_count).rjust(11, "0")

        self.commodity_footer = "CO"
        self.commodity_footer += self.CM_RECORD_COUNT
        self.commodity_footer += self.CA_RECORD_COUNT
        self.commodity_footer += "ME_RECORD_COUNT"
        self.commodity_footer += self.MD_RECORD_COUNT
        self.commodity_footer += "MX_RECORD_COUNT"
        self.commodity_footer += "TOTAL_RECORD_COUNT" + CommonString.line_feed

        self.icl_vme_file.write(self.commodity_footer)

    def write_footnotes(self):
        if self.WRITE_FOOTNOTES == 1:
            self.start_timer("Writing list of footnotes to ICL VME file")
            self.write_footnote_header()
            for footnote in self.footnotes:
                self.icl_vme_file.write(footnote.extract_line)
            self.write_footnote_footer()
            self.end_timer("Writing list of footnotes to ICL VME file")

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
        # Commodity code -> measure appender
        parser = Appender()
        parser.parse()
        parser.create_csv()
        sys.exit()

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
        self.get_measure_types_friendly()
        self.get_geographical_areas_friendly()
        self.get_additional_codes_friendly()
        self.get_seasonal_rates()
        # self.get_unmatched_supplementary_units()
        self.get_spvs()
        self.get_geographical_areas()
        self.get_supplementary_units_reference()
        self.load_pr_measures()

    def load_pr_measures(self):
        print("Getting PR measures")
        self.pr_measures = []
        filename = os.path.join(self.reference_folder, "pr.measures.txt")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                pr_measure = PrMeasure(row[0], row[1])
                self.pr_measures.append(pr_measure)
        pass

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

    def get_measure_types_friendly(self):
        sql = """select mt.measure_type_id, mtd.description
        from measure_types mt, measure_type_descriptions mtd
        where mt.measure_type_id = mtd.measure_type_id
        and mt.validity_end_date is null
        order by 1
        """
        self.measure_types_friendly = {}
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            self.measure_types_friendly[row[0]] = row[1]

    def get_additional_codes_friendly(self):
        sql = """SELECT acd1.additional_code_sid,
        acd1.additional_code_type_id::text || acd1.additional_code::text AS code,
        acd1.description
        FROM additional_code_descriptions acd1,
        additional_codes ac
        where ac.validity_end_date is null
        and ac.additional_code_sid = acd1.additional_code_sid AND (acd1.oid IN ( SELECT max(acd2.oid) AS max
        FROM additional_code_descriptions acd2
        WHERE acd1.additional_code_type_id::text = acd2.additional_code_type_id::text AND acd1.additional_code::text = acd2.additional_code::text))
        ORDER BY (acd1.additional_code_type_id::text || acd1.additional_code::text);
        """
        self.additional_codes_friendly = {}
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            self.additional_codes_friendly[row[0]] = row[2].replace('"', '')

    def get_geographical_areas_friendly(self):
        sql = """SELECT g.geographical_area_sid,
        geo1.geographical_area_id,
        geo1.description
        FROM geographical_area_descriptions geo1,
        geographical_areas g
        WHERE g.geographical_area_id::text = geo1.geographical_area_id::text
        AND (geo1.geographical_area_description_period_sid IN ( SELECT max(geo2.geographical_area_description_period_sid) AS max
        FROM geographical_area_descriptions geo2
        WHERE geo1.geographical_area_id::text = geo2.geographical_area_id::text))
        and g.validity_end_date is null
        ORDER BY geo1.geographical_area_id;"""
        self.geographical_areas_friendly = {}
        d = Database()
        rows = d.run_query(sql)
        for row in rows:
            description = f.null_to_string(row[2]).replace(",", "")
            self.geographical_areas_friendly[row[1]] = description

    def get_seasonal_rates(self):
        # Read the seasonal rates from the reference CSV and load to a global list
        print("Getting seasonal rates")
        self.seasonal_rates = []
        filename = os.path.join(self.reference_folder, "seasonal_rates.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                seasonal_rate = SeasonalRate(
                    row[0], row[1], row[2], row[3], row[4])
                self.seasonal_rates.append(seasonal_rate)

    def get_unmatched_supplementary_units(self):
        # This should not be run any more
        # Read the unmatched supplementary units from the reference CSV and load to a global list, needed for excise
        print("Getting unmatched supplementary units")
        self.unmatched_supplementary_units = []
        filename = os.path.join(self.reference_folder, "unmatched_supplementary_units.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                unmatched_supplementary_unit = UnmatchedSupplementaryUnit(row[0], row[1], row[2], row[4])
                self.unmatched_supplementary_units.append(unmatched_supplementary_unit)

    def get_spvs(self):
        print("Getting SPVs")
        # spv_handler = SPVHandler(self.SNAPSHOT_DATE)
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
        filename = os.path.join(self.reference_folder,
                                "supplementary_units.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                supplementary_unit = SupplementaryUnit(row[0], row[1], row[2])
                self.supplementary_units.append(supplementary_unit)
                self.supplementary_unit_dict[row[0] + row[1]] = row[2]

    def get_geographical_areas(self):
        print("Getting geographical areas")
        self.geographical_areas = []
        filename = os.path.join(self.reference_folder, "geographical_areas.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) >= 3:
                    geographical_area = GeographicalArea(
                        row[0], row[1], row[2])
                    self.geographical_areas.append(geographical_area)

    def create_delta(self):
        self.change_date = self.SNAPSHOT_DATE
        self.change_period = "week"
        self.delta = Delta()
