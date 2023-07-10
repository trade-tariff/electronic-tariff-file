import sys
from dotenv import load_dotenv
import time
import os
import ssl
from datetime import datetime, timedelta, date
import csv
import inquirer
from pathlib2 import Path

from classes.enums import CommonString
from classes.database import Database
from classes.commodity import Commodity
from classes.measure import Measure
from classes.measure_type import MeasureType, MeasureType2
from classes.additional_code import AdditionalCode
from classes.geographical_area import GeographicalArea, GeographicalArea2
from classes.certificate import Certificate
from classes.measure_component import MeasureComponent
from classes.measure_condition import MeasureCondition
from classes.measure_excluded_geographical_area import MeasureExcludedGeographicalArea
from classes.footnote import Footnote
from classes.commodity_footnote import CommodityFootnote
from classes.measure_footnote import MeasureFootnote
from classes.seasonal_rate import SeasonalRate
from classes.simplified_procedure_value import SimplifiedProcedureValue
from classes.quota_definition import QuotaDefinition, QuotaExclusion, QuotaCommodity
from classes.sendgrid_mailer import SendgridMailer
from classes.zipper import Zipper
from classes.delta import Delta
import classes.globals as g
from classes.functions import functions as f
from classes.sql_query import SqlQuery


class Tariff(object):
    def __init__(self):
        f.clear()
        self.message_string = ""
        self.create_ssl_unverified_context()
        self.get_config()
        self.get_scope()
        self.get_date()
        self.get_folders()

        # self.get_all_quotas()
        self.get_all_additional_codes()
        self.get_all_geographies()
        self.get_measure_types()
        self.get_measure_types_lookup()
        self.get_geographical_areas_lookup()
        self.get_supplementary_units_reference()
        self.get_footnotes()
        self.get_commodity_footnotes()
        self.get_spvs()
        self.get_commodity_codes()
        self.get_ancestry()
        self.get_seasonal_rates()
        self.get_measures()
        self.get_measure_footnotes()
        self.get_measure_components()
        self.get_measure_conditions()
        self.get_measure_excluded_geographical_areas()
        self.assign_measure_components()
        self.assign_measure_conditions()
        self.get_measure_groups()
        self.create_commodity_dict()
        self.check_export_umbrella()
        self.assign_commodity_footnotes()
        self.assign_measures()
        for c in g.commodities_dict:
            g.commodities_dict[c].get_commodity_type()
            if g.commodities_dict[c].writable:
                g.commodities_dict[c].get_supplementary_units()
                g.commodities_dict[c].get_seasonal_rate()
                g.commodities_dict[c].check_end_use()
                g.commodities_dict[c].get_ancestral_descriptions()
                g.commodities_dict[c].get_additional_code_string()
                g.commodities_dict[c].get_measure_records()
                g.commodities_dict[c].sort_measures()

        self.write_icl_vme_file()
        self.list_measure_types_not_found()
        self.write_commodities_csv()
        if self.WRITE_ANCILLARY_FILES:
            self.get_all_footnotes()
            self.get_all_certificates()
            self.get_all_quotas()
            self.write_all_geographies()
            self.write_all_additional_codes()
            self.write_measure_types()

        self.create_delta()
        self.zip_and_upload()
        self.create_email_message()
        self.send_email_message()

    def list_measure_types_not_found(self):
        measure_types = ", ".join(g.measure_types_not_found)
        print("\nMeasure types not found: {measure_types}\n\n".format(measure_types=measure_types))

    def create_ssl_unverified_context(self):
        ssl._create_default_https_context = ssl._create_unverified_context

    def get_date(self):
        if len(sys.argv) > 2:
            d = sys.argv[2].lower()
            date_format = "%Y-%m-%d"
            try:
                datetime.strptime(d, date_format)
                g.SNAPSHOT_DATE = d
                g.COMPARISON_DATE = datetime.strptime(d, '%Y-%m-%d') - timedelta(days=7)
                d2 = datetime.strptime(d, '%Y-%m-%d')
                g.SNAPSHOT_DAY = d2.strftime('%d')
                g.SNAPSHOT_MONTH = d2.strftime('%m')
                g.SNAPSHOT_YEAR = d2.strftime('%Y')

            except ValueError:
                print("This is the incorrect date string format. It should be YYYY-MM-DD")
                sys.exit()
        else:
            d = datetime.now()
            g.SNAPSHOT_DATE = d.strftime('%Y-%m-%d')
            g.COMPARISON_DATE = d - timedelta(days=7)

            g.SNAPSHOT_DAY = d.strftime('%d')
            g.SNAPSHOT_MONTH = d.strftime('%m')
            g.SNAPSHOT_YEAR = d.strftime('%Y')

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
            g.DATABASE = os.getenv('DATABASE_UK')
        else:
            g.DATABASE = os.getenv('DATABASE_EU')

    def get_config(self):
        load_dotenv('.env')
        self.use_materialized_views = int(os.getenv('USE_MATERIALIZED_VIEWS'))
        self.min_code = os.getenv('MIN_CODE')
        self.max_code = os.getenv('MAX_CODE')
        if self.min_code != "0000000000" or self.max_code != "9999999999":
            g.complete_tariff = False
        else:
            g.complete_tariff = True

        self.BUCKET_NAME = os.getenv('BUCKET_NAME')
        self.bucket_url = "https://" + self.BUCKET_NAME + ".s3.amazonaws.com/"
        self.bucket_url = "https://reporting.trade-tariff.service.gov.uk/"

        self.WRITE_MEASURES = int(os.getenv('WRITE_MEASURES'))
        self.WRITE_ADDITIONAL_CODES = int(os.getenv('WRITE_ADDITIONAL_CODES'))
        self.WRITE_FOOTNOTES = int(os.getenv('WRITE_FOOTNOTES'))
        self.WRITE_ANCILLARY_FILES = int(os.getenv('WRITE_ANCILLARY_FILES'))
        self.DEBUG_OVERRIDE = int(os.getenv('DEBUG_OVERRIDE'))
        self.PLACEHOLDER_FOR_EMPTY_DESCRIPTIONS = os.getenv('PLACEHOLDER_FOR_EMPTY_DESCRIPTIONS')
        self.VSCODE_DEBUG_MODE = os.getenv('VSCODE_DEBUG_MODE')

        # There is only any point in writing to AWS & sending a mail
        # if both ZIP variables are set
        self.CREATE_7Z = f.get_config_key('CREATE_7Z', "int", 0)
        self.CREATE_ZIP = f.get_config_key('CREATE_ZIP', "int", 0)
        if self.CREATE_7Z == 0 or self.CREATE_ZIP == 0:
            self.WRITE_TO_AWS = 0
            self.SEND_MAIL = 0
        else:
            # We will only ever send the email if write to AWS is set to true
            self.WRITE_TO_AWS = f.get_config_key('WRITE_TO_AWS', "int", 0)
            self.SEND_MAIL = f.get_config_key('SEND_MAIL', "int", 0)
            if self.WRITE_TO_AWS == 0:
                self.SEND_MAIL = 0

        # Put in protection in case the min / max codes are accidentally set to
        # values other than 0000000000 and 9999999999. If you do proceed, then the application will not
        # load any data to AWS or send the email.
        if not g.complete_tariff:
            self.SEND_MAIL = False
            self.WRITE_TO_AWS = False
            message = "The lowest code that this will be run against is {min_code} and the highest is {max_code}\n\n".format(
                min_code=self.min_code,
                max_code=self.max_code
            )
            message += "If you choose to continue, then:\n\n- no files will be uploaded to AWS\n- no email will be sent.\n\n"
            question = "Are you sure you want to continue?\n\n"
            if f.yesno_question(message, question) is False:
                sys.exit()
        else:
            # Check that we want to proceed even if the variables to load
            # to AWS and / or to senf an email are not set
            if self.SEND_MAIL == 0 or self.WRITE_TO_AWS == 0:
                msg = ""
                if self.WRITE_TO_AWS == 0:
                    msg += "The WRITE_TO_AWS flag is set to 0\n"
                if self.SEND_MAIL == 0:
                    msg += "The SEND_MAIL flag is set to 0\n"
                print(msg)
                msg = "Are you sure you want to continue?\n\n"

                questions = [
                    inquirer.Confirm("proceed_with_messaging_status", message=msg, default=True),
                ]
                answers = inquirer.prompt(questions)
                if answers["proceed_with_messaging_status"] is False:
                    sys.exit()

    def get_folders(self):
        self.current_folder = os.getcwd()
        self.data_folder = os.path.join(self.current_folder, "data")
        self.reference_folder = os.path.join(self.data_folder, "reference")
        self.data_in_folder = os.path.join(self.data_folder, "in")
        self.data_out_folder = os.path.join(self.data_folder, "out")
        self.export_folder = os.path.join(self.current_folder, "_export")
        self.documentation_folder = os.path.join(self.current_folder, "documentation")
        self.documentation_file = os.path.join(self.documentation_folder, "Documentation on tariff CSV data files.docx")
        self.correlation_file = os.path.join(self.documentation_folder, "Ascii file and CDS measure type correlation table 1.1.docx")

        self.filename = "hmrc-tariff-ascii-" + g.SNAPSHOT_DATE + ".txt"

        # Make the export folder
        os.makedirs(self.export_folder, exist_ok=True)

        # Make the date-specific folder
        date_time_obj = datetime.strptime(g.SNAPSHOT_DATE, '%Y-%m-%d')
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
        g.delta_folder = os.path.join(self.scope_folder, "delta")
        self.log_folder = os.path.join(self.scope_folder, "logs")
        self.log_filename = os.path.join(self.log_folder, "etf_creation_log.txt")

        os.makedirs(self.icl_vme_folder, exist_ok=True)
        os.makedirs(self.csv_folder, exist_ok=True)
        os.makedirs(g.delta_folder, exist_ok=True)
        os.makedirs(self.log_folder, exist_ok=True)

        # Work out the path to the ICL VME extract
        self.filepath_icl_vme = os.path.join(self.icl_vme_folder, self.filename)

        # Measures CSV extract filename
        self.measure_csv_filename = self.filename.replace(".txt", ".csv")
        self.measure_csv_filename = self.measure_csv_filename.replace("ascii", "measures")
        self.measure_csv_filepath = os.path.join(self.csv_folder, self.measure_csv_filename)

        # Commodities CSV extract filename
        self.commodity_csv_filename = self.measure_csv_filename.replace("measures", "commodities")
        self.commodity_csv_filepath = os.path.join(self.csv_folder, self.commodity_csv_filename)

        if self.WRITE_ANCILLARY_FILES:
            # MFN (103 / 105) CSV extract filename
            self.mfn_csv_filename = self.filename.replace(".txt", ".csv")
            self.mfn_csv_filename = self.mfn_csv_filename.replace("ascii", "mfn")
            self.mfn_csv_filepath = os.path.join(self.csv_folder, self.mfn_csv_filename)

            # Supplementary units (109, 110, 111)
            self.supplementary_units_csv_filename = self.filename.replace(".txt", ".csv")
            self.supplementary_units_csv_filename = self.supplementary_units_csv_filename.replace("ascii", "supplementary_units")
            self.supplementary_units_csv_filepath = os.path.join(self.csv_folder, self.supplementary_units_csv_filename)

            # Footnotes CSV extract filename
            self.footnote_csv_filename = self.measure_csv_filename.replace("measures", "footnotes")
            self.footnote_csv_filepath = os.path.join(self.csv_folder, self.footnote_csv_filename)

            # Certificates CSV extract filename
            self.certificate_csv_filename = self.measure_csv_filename.replace("measures", "certificates")
            self.certificate_csv_filepath = os.path.join(self.csv_folder, self.certificate_csv_filename)

            # Quotas CSV extract filename
            self.quota_csv_filename = self.measure_csv_filename.replace("measures", "quotas")
            self.quota_csv_filepath = os.path.join(self.csv_folder, self.quota_csv_filename)

            # Geography CSV extract filename
            self.geography_csv_filename = self.measure_csv_filename.replace("measures", "geography")
            self.geography_csv_filepath = os.path.join(self.csv_folder, self.geography_csv_filename)

            # Measure type CSV extract filename
            self.measure_type_csv_filename = self.measure_csv_filename.replace("measures", "measure_type")
            self.measure_type_csv_filepath = os.path.join(self.csv_folder, self.measure_type_csv_filename)

            # Additional code CSV extract filename
            self.additional_code_csv_filename = self.measure_csv_filename.replace("measures", "additional_code")
            self.additional_code_csv_filepath = os.path.join(self.csv_folder, self.additional_code_csv_filename)

    def get_geographical_areas_lookup(self):
        self.start_timer("Getting geographical areas")
        g.geographical_areas = []
        filename = os.path.join(self.reference_folder, "geographical_areas.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) >= 3:
                    geographical_area = GeographicalArea(row[0], row[1], row[2])
                    g.geographical_areas.append(geographical_area)

        self.end_timer("Getting geographical areas")

    def get_measure_types_lookup(self):
        self.start_timer("Getting measure types")
        g.measure_types = {}
        filename = os.path.join(self.reference_folder, "measure_types.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) >= 4:
                    measure_type = MeasureType(row[0], row[1], row[2], row[3])
                    g.measure_types[row[0]] = measure_type
        self.end_timer("Getting measure types")

    def get_supplementary_units_reference(self):
        self.start_timer("Getting supplementary units")
        g.supplementary_unit_dict = {}
        filename = os.path.join(self.reference_folder, "supplementary_units.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                g.supplementary_unit_dict[row[0] + row[1]] = row[2]
        self.end_timer("Getting supplementary units")

    def get_footnotes(self):
        # Gets ONLY commodity code related footnotes, not measure-related ones

        # Problem with footnotes is the size of the fields
        # They are identified by 5 digits in the TAP / CDS feed
        # but only by three in the data from CHIEF - therefore we need a kludge massage:
        # The answer is
        # Any footnotes beginning with NC - add 800 to the IDs:
        # Any footnotes beginning with PN - add 900 to the IDs:
        # Any footnotes beginning with TN - as-is
        # This gets round the possible duplication on the three digits:

        self.start_timer("Getting footnotes")
        g.footnotes = []
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
            footnote.FOOTNOTE_EDATE = f.YYYYMMDD(row[3])
            footnote.FOOTNOTE_LDATE = f.YYYYMMDD(row[4])
            footnote.FOOTNOTE_TEXT = row[2]
            footnote.get_footnote_number()
            footnote.format_text()
            g.footnotes.append(footnote)

        self.end_timer("Getting footnotes")

    def get_commodity_footnotes(self):
        # Gets the association of footnotes to commodities
        self.start_timer("Getting commodity-level footnote associations")
        g.commodity_footnotes = []
        g.commodities_with_footnotes = []
        sql = """
        with cer as (
            select gn.goods_nomenclature_item_id, gn.goods_nomenclature_sid,
            fagn.footnote_type as footnote_type_id, fagn.footnote_id
            from footnote_association_goods_nomenclatures fagn, goods_nomenclatures gn
            where fagn.goods_nomenclature_sid = gn.goods_nomenclature_sid
            and fagn.validity_end_date is null
            and gn.validity_end_date is null
            and gn.validity_start_date <= %s
            and (gn.validity_end_date >= %s or gn.validity_end_date is null)
            and fagn.validity_start_date <= %s
            and (fagn.validity_end_date >= %s or fagn.validity_end_date is null)
            order by gn.goods_nomenclature_item_id, fagn.footnote_type, fagn.footnote_id
        ) select * from cer
        where cer.goods_nomenclature_item_id not in (select goods_nomenclature_item_id from hidden_goods_nomenclatures);
        """
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        d = Database()
        rows = d.run_query(sql, params)
        for row in rows:
            footnote = CommodityFootnote()
            footnote.goods_nomenclature_item_id = row[0]
            footnote.goods_nomenclature_sid = row[1]
            footnote.footnote_type_id = row[2]
            footnote.footnote_id = row[3]
            footnote.get_footnote_number()
            g.commodity_footnotes.append(footnote)
            g.commodities_with_footnotes.append(footnote.goods_nomenclature_sid)

        g.commodities_with_footnotes = set(g.commodities_with_footnotes)

        self.end_timer("Getting commodity-level footnote associations")

    def get_measure_footnotes(self):
        # Gets the association of footnotes to measures
        self.start_timer("Getting measure-level footnote associations")
        g.measure_footnotes = []
        if self.use_materialized_views:
            sql = SqlQuery("measure_footnotes", "get_measure_footnotes_mv.sql").sql
        else:
            sql = SqlQuery("measure_footnotes", "get_measure_footnotes.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            self.min_code,
            self.max_code
        ]
        rows = d.run_query(sql, params)
        for row in rows:
            footnote = MeasureFootnote()
            footnote.measure_sid = row[0]
            footnote.footnote = row[1]
            g.measure_footnotes.append(footnote)
            self.measures_dict[footnote.measure_sid].footnotes.append(footnote.footnote)

        self.end_timer("Getting measure-level footnote associations")

    def get_measure_excluded_geographical_areas(self):
        # Get measure geographical area exclusions
        self.start_timer("Getting measure excluded geographical areas")
        self.measure_excluded_geographical_areas = []
        if self.use_materialized_views:
            sql = SqlQuery("excluded_geographical_areas", "get_measure_excluded_geographical_areas_mv.sql").sql
        else:
            sql = SqlQuery("excluded_geographical_areas", "get_measure_excluded_geographical_areas.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
        for row in rows:
            measure_excluded_geographical_area = MeasureExcludedGeographicalArea()
            measure_excluded_geographical_area.measure_sid = row[0]
            measure_excluded_geographical_area.excluded_geographical_area = row[1]
            measure_excluded_geographical_area.geographical_area_sid = row[2]

            self.measure_excluded_geographical_areas.append(measure_excluded_geographical_area)

        # Assign the exclusions to the measures
        for mega in self.measure_excluded_geographical_areas:
            self.measures_dict[mega.measure_sid].measure_excluded_geographical_areas.append(mega)

        self.end_timer("Getting measure excluded geographical areas")

    def assign_commodity_footnotes(self):
        self.start_timer("Assigning footnotes to commodities")
        for footnote_association in g.commodity_footnotes:
            g.commodities_dict[footnote_association.goods_nomenclature_sid].footnotes.append(footnote_association)

        for commodity in self.commodities:
            commodity.append_footnotes_to_description()

        self.end_timer("Assigning footnotes to commodities")

    def get_seasonal_rates(self):
        # Read the seasonal rates from the reference CSV and load to a global list
        self.start_timer("Getting seasonal rates")
        g.seasonal_rates = []
        filename = os.path.join(self.reference_folder, "seasonal_rates.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                seasonal_rate = SeasonalRate(row[0], row[1], row[2], row[3], row[4])
                g.seasonal_rates.append(seasonal_rate)

        # Get the IDs of the comm code tiers included
        for rate in g.seasonal_rates:
            for commodity in self.commodities:
                if commodity.goods_nomenclature_item_id == rate.goods_nomenclature_item_id and commodity.productline_suffix == "80":
                    rate.goods_nomenclature_sid = commodity.goods_nomenclature_sid
                    break

        self.end_timer("Getting seasonal rates")

    def get_spvs(self):
        self.start_timer("Getting SPVs")
        g.spvs = []
        filename = os.path.join(self.reference_folder, "spvs.csv")
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                spv = SimplifiedProcedureValue(row[0], row[1])
                g.spvs.append(spv)

        self.end_timer("Getting SPVs")

    def get_commodity_codes(self):
        self.start_timer("Getting commodity codes")
        if self.use_materialized_views:
            sql = SqlQuery("commodity_codes", "get_commodity_codes_mv.sql").sql
        else:
            sql = SqlQuery("commodity_codes", "get_commodity_codes.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            self.min_code,
            self.max_code
        ]
        rows = d.run_query(sql, params)
        self.commodities = []
        g.commodities_dict = {}
        index = 0
        for row in rows:
            index += 1
            commodity = Commodity(row)
            self.commodities.append(commodity)

        self.end_timer("Getting commodity codes")

    def get_measures(self):
        measure_compound_keys = []
        self.start_timer("Getting measures")
        if self.use_materialized_views:
            sql = SqlQuery("measures", "get_measures_mv.sql").sql
        else:
            sql = SqlQuery("measures", "get_measures.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            self.min_code,
            self.max_code
        ]
        rows = d.run_query(sql, params)
        self.measures_dict = {}
        if len(rows) == 0:
            print("Data error - check 'get_measures' SQL")
            sys.exit()
        for row in rows:
            m = Measure(row)
            if m.is_trade_remedy:
                if m.compound_key in measure_compound_keys:
                    m.is_duplicate = True
                else:
                    measure_compound_keys.append(m.compound_key)

            self.measures_dict[m.measure_sid] = m

        self.end_timer("Getting measures")

    def get_measure_components(self):
        self.start_timer("Getting measure components")
        if self.use_materialized_views:
            sql = SqlQuery("measure_components", "get_measure_components_mv.sql").sql
        else:
            sql = SqlQuery("measure_components", "get_measure_components.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            self.min_code,
            self.max_code
        ]
        rows = d.run_query(sql, params)
        self.measure_components = []
        for row in rows:
            mc = MeasureComponent(row)
            self.measure_components.append(mc)

        self.end_timer("Getting measure components")

    def get_measure_conditions(self):
        self.start_timer("Getting measure conditions")
        if self.use_materialized_views:
            sql = SqlQuery("measure_conditions", "get_measure_conditions_mv.sql").sql
        else:
            sql = SqlQuery("measure_conditions", "get_measure_conditions.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            self.min_code,
            self.max_code
        ]
        rows = d.run_query(sql, params)
        self.measure_conditions = []
        for row in rows:
            mc = MeasureCondition(row)
            self.measure_conditions.append(mc)

        self.end_timer("Getting measure conditions")

    def assign_measure_conditions(self):
        self.start_timer("Assigning measure conditions to measures")
        for mc in self.measure_conditions:
            if mc.certificate != "":
                self.measures_dict[mc.measure_sid].measure_conditions.append(mc)
                self.measures_dict[mc.measure_sid].certificates.append(mc.certificate)

        self.get_ex_head()
        self.end_timer("Assigning measure conditions to measures")

    def get_measure_groups(self):
        for m in self.measures_dict:
            self.measures_dict[m].get_measure_group_code()
            self.measures_dict[m].get_geographical_area_codes()
            self.measures_dict[m].determine_origin_add_charge()
            self.measures_dict[m].determine_destination_country_groups()

    def get_ex_head(self):
        for m in self.measures_dict:
            self.measures_dict[m].get_ex_head()

    def assign_measure_components(self):
        self.start_timer("Assigning measure components to measures")
        for mc in self.measure_components:
            self.measures_dict[mc.measure_sid].measure_components.append(mc)

        # Create the duty fields on the ICL VME export
        for m in self.measures_dict:
            index = -1
            for mc in self.measures_dict[m].measure_components:
                index += 1
                self.measures_dict[m].duty_records[index] = mc.cts_component_definition

            self.measures_dict[m].get_duty_type()
        self.end_timer("Assigning measure components to measures")

    def create_commodity_dict(self):
        for c in self.commodities:
            g.commodities_dict[c.goods_nomenclature_sid] = c

    def assign_measures(self):
        # Assign the measures to the commodities
        self.start_timer("Assign the measures to the commodities")
        for m in self.measures_dict:
            measure_sid = self.measures_dict[m].measure_sid
            if measure_sid not in g.commodities_dict[self.measures_dict[m].goods_nomenclature_sid].measure_sids:
                g.commodities_dict[self.measures_dict[m].goods_nomenclature_sid].measures.append(self.measures_dict[m])
                g.commodities_dict[self.measures_dict[m].goods_nomenclature_sid].measure_sids.append(self.measures_dict[m].measure_sid)

        # Inherit the measures to the end lines that share them
        self.end_timer("Assign the measures to the commodities")

        self.start_timer("Inherit the measures to the end lines that share them")
        for c in g.commodities_dict:
            if g.commodities_dict[c].writable:
                if len(g.commodities_dict[c].ancestors) > 0:
                    for ancestor in g.commodities_dict[c].ancestors:
                        for m in g.commodities_dict[ancestor].measures:
                            if m.measure_sid not in g.commodities_dict[c].measure_sids:
                                g.commodities_dict[c].measure_sids.append(m.measure_sid)
                                g.commodities_dict[c].measures.append(m)
                        # g.commodities_dict[c].measures += g.commodities_dict[ancestor].measures
        self.end_timer("Inherit the measures to the end lines that share them")

    def print_commodities(self):
        for c in self.commodities:
            print(c)

    def get_ancestry(self):
        for i in range(0, len(self.commodities)):
            c = self.commodities[i]
            # Get end line
            if i == len(self.commodities) - 1:
                c.end_line = True
            else:
                if i < len(self.commodities) - 1:
                    c2 = self.commodities[i + 1]
                    if c2.number_indents <= c.number_indents:
                        c.end_line = True
                    else:
                        c.end_line = False
                else:
                    c.end_line = False

            # Get ancestors
            running_indent_for_ancestors = c.number_indents
            if running_indent_for_ancestors > 0:
                for j in range(i - 1, -1, -1):
                    c2 = self.commodities[j]
                    if c2.number_indents < running_indent_for_ancestors:
                        c.ancestors.append(c2.goods_nomenclature_sid)
                        running_indent_for_ancestors = c2.number_indents
                    if c2.chapter != c.chapter:
                        break

        # Get children
        for i in range(0, len(self.commodities)):
            c = self.commodities[i]
            for j in range(i + 1, len(self.commodities)):
                c2 = self.commodities[j]
                if c2.number_indents == c.number_indents + 1:
                    c.children.append(c2.goods_nomenclature_sid)
                elif c2.number_indents <= c.number_indents:
                    break

    def check_export_umbrella(self):
        for c in self.commodities:
            c.check_export_umbrella()
            c.check_writable()

    def get_commodity_header(self):
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
        self.commodity_header += f.YYYYMMDD(datetime.now())
        self.commodity_header += f.HHMMSS(datetime.now())
        self.commodity_header += year
        self.commodity_header += week_num

    def update_commodity_control_record(self):
        self.TOTAL_RECORD_COUNT = self.CM_RECORD_COUNT + self.CA_RECORD_COUNT + self.ME_RECORD_COUNT + self.MD_RECORD_COUNT + self.MX_RECORD_COUNT + self.TOTAL_RECORD_COUNT
        self.commodity_control_record = "CO"
        self.commodity_control_record += str(self.CM_RECORD_COUNT).zfill(7)
        self.commodity_control_record += str(self.CA_RECORD_COUNT).zfill(7)
        self.commodity_control_record += str(self.ME_RECORD_COUNT).zfill(7)
        self.commodity_control_record += str(self.MD_RECORD_COUNT).zfill(7)
        self.commodity_control_record += "MXCOUNT"  # str(self.MX_RECORD_COUNT).zfill(7)
        self.commodity_control_record += "TOTAL_COUNT"  # str(self.TOTAL_RECORD_COUNT).zfill(11)

    def write_icl_vme_file(self):
        self.start_timer("Writing commodities")
        f = open(self.filepath_icl_vme, "w")
        field_names = ["commodity__sid", "commodity__code", "measure__sid", "measure__type__id", "measure__type__description", "measure__additional_code__code", "measure__additional_code__description", "measure__duty_expression",
                       "measure__effective_start_date", "measure__effective_end_date", "measure__reduction_indicator", "measure__footnotes", "measure__conditions", "measure__geographical_area__sid", "measure__geographical_area__id",
                       "measure__geographical_area__description", "measure__excluded_geographical_areas__ids", "measure__excluded_geographical_areas__descriptions", "measure__quota__order_number", "trade__direction"]
        measure_file_header_row = ",".join(field_names) + CommonString.line_feed

        measure_csv_file = open(self.measure_csv_filepath, "w+")
        measure_csv_file.write(measure_file_header_row)

        if self.WRITE_ANCILLARY_FILES:
            mfn_csv_file = open(self.mfn_csv_filepath, "w+")
            mfn_csv_file.write(measure_file_header_row)
            supplementary_units_csv_file = open(self.supplementary_units_csv_filepath, "w+")
            supplementary_units_csv_file.write(measure_file_header_row)

        # Write the main header record
        self.get_commodity_header()
        f.write(self.commodity_header + "\n")

        # Set all counts to zero
        self.CM_RECORD_COUNT = 0
        self.CA_RECORD_COUNT = 0
        self.ME_RECORD_COUNT = 0
        self.MD_RECORD_COUNT = 0
        self.MX_RECORD_COUNT = 0
        self.TOTAL_RECORD_COUNT = 0

        # Write the commodities
        for c in g.commodities_dict:
            g.commodities_dict[c].get_commodity_record()
            if g.commodities_dict[c].writable:
                self.CM_RECORD_COUNT += 1
                # Write the commodity code record
                f.write(g.commodities_dict[c].commodity_record + "\n")

                # Write the commodity's additional code string
                if self.WRITE_ADDITIONAL_CODES:
                    if g.commodities_dict[c].additional_code_string != "":
                        self.CA_RECORD_COUNT += 1
                        f.write(g.commodities_dict[c].additional_code_string + "\n")

                # Write the commodity's measures
                if self.WRITE_MEASURES:
                    for m in g.commodities_dict[c].measures:
                        tmp = m.measure_record_for_csv
                        tmp = tmp.replace("GOODS_NOMENCLATURE_SID", str(g.commodities_dict[c].goods_nomenclature_sid))
                        tmp = tmp.replace("GOODS_NOMENCLATURE_ITEM_ID", g.commodities_dict[c].goods_nomenclature_item_id)
                        if g.commodities_dict[c].end_line:
                            measure_csv_file.write(tmp + "\n")
                            if self.WRITE_ANCILLARY_FILES:
                                if m.is_mfn:
                                    if m.geographical_area_id == "1011":
                                        mfn_csv_file.write(tmp + "\n")
                                elif m.is_supplementary_unit:
                                    supplementary_units_csv_file.write(tmp + "\n")
                        if m.measure_record != "":
                            if m.ORIGIN_COUNTRY_GROUP_CODE == "EXPAND":
                                for member in m.members:
                                    self.ME_RECORD_COUNT += 1
                                    tmp = m.measure_record.replace("EXPAND", member + "    ")
                                    f.write(tmp + "\n")
                            else:
                                self.ME_RECORD_COUNT += 1
                                f.write(m.measure_record + "\n")
                                if len(m.measure_excluded_geographical_areas) > 0:
                                    for mega in m.measure_excluded_geographical_areas:
                                        self.MX_RECORD_COUNT += 1
                                        if m.measure_template != "":
                                            f.write(m.measure_template.replace("$$", mega.excluded_geographical_area) + "\n")

        self.update_commodity_control_record()
        f.write(self.commodity_control_record + "\n")
        measure_csv_file.close()
        if self.WRITE_ANCILLARY_FILES:
            mfn_csv_file.close()
            supplementary_units_csv_file.close()

        # Write the footnotes
        if self.WRITE_FOOTNOTES:
            self.get_footnote_header()
            self.get_footnote_footer()
            f.write(self.footnote_header + "\n")

            for fn in g.footnotes:
                fn.create_extract_line()
                f.write(fn.extract_line + "\n")

            f.write(self.footnote_footer + "\n")

        # Close the file
        f.close()
        self.end_timer("Writing commodities")
        self.update_counts()

    def update_counts(self):
        file1 = open(self.filepath_icl_vme, 'r')
        count = 0
        self.CM_RECORD_COUNT = 0
        self.CA_RECORD_COUNT = 0
        self.ME_RECORD_COUNT = 0
        self.MD_RECORD_COUNT = 0
        self.MX_RECORD_COUNT = 0
        self.TOTAL_RECORD_COUNT = 0

        while True:
            count += 1

            # Get next line from file
            line = file1.readline()

            # if line is empty
            # end of file is reached
            if not line:
                break
            if len(line) < 2:
                print("Short line on {line}".format(line=str(count)))
                break

            if line[0:2] == "CM":
                self.CM_RECORD_COUNT += 1
            elif line[0:2] == "CA":
                self.CA_RECORD_COUNT += 1
            elif line[0:2] == "ME":
                self.ME_RECORD_COUNT += 1
            elif line[0:2] == "MX":
                self.MX_RECORD_COUNT += 1
            elif line[0:2] == "MD":
                self.MD_RECORD_COUNT += 1

        self.TOTAL_RECORD_COUNT = self.CM_RECORD_COUNT + self.CA_RECORD_COUNT + self.ME_RECORD_COUNT + self.MX_RECORD_COUNT + self.MD_RECORD_COUNT

        file1.close()
        print(str(count))
        print("Commodity records = {x}".format(x=str(self.CM_RECORD_COUNT)))
        print("Add code records = {x}".format(x=str(self.CA_RECORD_COUNT)))
        print("Measure records = {x}".format(x=str(self.ME_RECORD_COUNT)))
        print("Exception records = {x}".format(x=str(self.MX_RECORD_COUNT)))
        print("Total records = {x}".format(x=str(self.TOTAL_RECORD_COUNT)))

        path = Path(self.filepath_icl_vme)
        text = path.read_text()
        text = text.replace("MXCOUNT", str(self.MX_RECORD_COUNT).zfill(7))
        text = text.replace("TOTAL_COUNT", str(self.TOTAL_RECORD_COUNT).zfill(11))
        path.write_text(text)

    def get_footnote_header(self):
        # HF2020121500000021001
        # RECORD-TYPE 2
        # DATE-CREATED 8
        # TIME-CREATED 6
        # RUN-NUMBER 5
        today = datetime.now()
        my_year = today.strftime("%y")
        my_week = str(today.isocalendar()[1]).zfill(3)
        self.footnote_header = "HF"
        self.footnote_header += f.YYYYMMDD(datetime.now())
        self.footnote_header += f.HHMMSS(datetime.now())
        self.footnote_header += my_year + my_week

    def get_footnote_footer(self):
        # CF0000120
        # RECORD-TYPE 2
        # FOOTNOTE-RECORD-COUNT 7
        self.footnote_footer = "CF"
        self.footnote_footer += str(len(g.footnotes)).zfill(7)

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

    def get_all_footnotes(self):
        self.footnote_csv_file = open(self.footnote_csv_filepath, "w+")
        self.footnote_csv_file.write('"footnote__id","footnote__description","start__date","end__date","footnote__type"' + CommonString.line_feed)
        self.start_timer("Getting and writing all footnotes for CSV export")
        self.measures = []
        if self.use_materialized_views:
            sql = SqlQuery("footnotes_all", "get_footnotes_mv.sql").sql
        else:
            sql = SqlQuery("footnotes_all", "get_footnotes.sql").sql

        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
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
        self.certificate_csv_file = open(self.certificate_csv_filepath, "w+")
        self.certificate_csv_file.write('"certificate__id","certificate__description","start__date","end__date"' + CommonString.line_feed)
        self.measures = []
        if self.use_materialized_views:
            sql = SqlQuery("certificates", "get_certificates_mv.sql").sql
        else:
            sql = SqlQuery("certificates", "get_certificates.sql").sql

        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
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

    def get_measure_types(self):
        self.start_timer("Getting all measure types for CSV export")
        self.measure_type_csv_file = open(self.measure_type_csv_filepath, "w+")
        self.measure_type_csv_file.write('"measure_type_id","description"' + CommonString.line_feed)
        if self.use_materialized_views:
            sql = SqlQuery("measure_types", "get_measure_types_mv.sql").sql
        else:
            sql = SqlQuery("measure_types", "get_measure_types.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
        self.measure_types = []
        for row in rows:
            measure_type = MeasureType2()
            measure_type.measure_type_id = row[0]
            measure_type.description = row[1]
            measure_type.get_csv_string()

            self.measure_types.append(measure_type)

        self.end_timer("Getting all measure types for CSV export")
        self.measure_type_csv_file.close()

    def write_measure_types(self):
        self.start_timer("Writing measure types for CSV export")
        self.measure_type_csv_file = open(self.measure_type_csv_filepath, "w+")
        self.measure_type_csv_file.write('"measure_type_id","description"' + CommonString.line_feed)

        for measure_type in self.measure_types:
            self.measure_type_csv_file.write(measure_type.csv_string)

        self.end_timer("Writing measure types for CSV export")
        self.measure_type_csv_file.close()

    def write_all_additional_codes(self):
        self.start_timer("Writing all additional codes for CSV export")
        self.additional_code_csv_file = open(self.additional_code_csv_filepath, "w+")
        self.additional_code_csv_file.write('"additional code","description","start date","end date","type description"' + CommonString.line_feed)

        for additional_code in self.all_additional_codes:
            self.additional_code_csv_file.write(additional_code.csv_string)

        self.end_timer("Writing all additional codes for CSV export")
        self.additional_code_csv_file.close()

    def get_all_additional_codes(self):
        self.start_timer("Getting all additional codes for CSV export")
        if self.use_materialized_views:
            sql = SqlQuery("additional_codes", "get_additional_codes_mv.sql").sql
        else:
            sql = SqlQuery("additional_codes", "get_additional_codes.sql").sql
        d = Database()
        params = [
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
        self.all_additional_codes = []
        g.all_additional_codes_dict = {}
        for row in rows:
            additional_code = AdditionalCode()
            additional_code.code = row[0]
            additional_code.description = f.strip_quotes(row[1])
            additional_code.validity_start_date = f.format_date(row[2], "%Y-%m-%d")
            additional_code.validity_end_date = f.format_date(row[3], "%Y-%m-%d")
            additional_code.additional_code_type_description = f.strip_quotes(row[4])

            additional_code.get_csv_string()

            self.all_additional_codes.append(additional_code)
            g.all_additional_codes_dict[additional_code.code] = additional_code

        self.end_timer("Getting all additional codes for CSV export")

    def get_all_quotas(self):
        if self.scope == "xi":
            quota_order_number_range = "09"
        else:
            quota_order_number_range = "05"
        quota_order_number_range_licenced = quota_order_number_range + "4"
        self.start_timer("Getting and writing all quota definitions for CSV export")
        self.quota_csv_file = open(self.quota_csv_filepath, "w+")
        self.quota_csv_file.write(
            '"quota__order__number__id","definition__start__date","definition__end__date","initial__volume","unit","critical__state","critical__threshold","quota__type","origins","origin__exclusions","commodities"' + CommonString.line_feed
        )
        self.quota_commodities = []

        if self.use_materialized_views:
            sql = SqlQuery("quota_commodities", "get_quota_commodities_mv.sql").sql
        else:
            sql = SqlQuery("quota_commodities", "get_quota_commodities.sql").sql
        d = Database()
        params = [
            quota_order_number_range,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
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

        if self.use_materialized_views:
            sql = SqlQuery("quota_definitions", "get_quota_definitions_mv.sql").sql
        else:
            sql = SqlQuery("quota_definitions", "get_quota_definitions.sql").sql
        d = Database()
        params = [
            quota_order_number_range,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE,
            quota_order_number_range_licenced,
            g.SNAPSHOT_DATE,
            g.SNAPSHOT_DATE
        ]
        rows = d.run_query(sql, params)
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

    def get_all_geographies(self):
        self.start_timer("Getting all geographical areas for CSV export")
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
            and gam.validity_start_date <= '""" + g.SNAPSHOT_DATE + """'
            and (gam.validity_end_date is null or gam.validity_end_date > '""" + g.SNAPSHOT_DATE + """')
        )
        select g.geographical_area_sid, g.geographical_area_id, g.description, g.area_type,
        string_agg(distinct g2.child_id, '|' order by g2.child_id) as members
        from cte_geography g
        left outer join cte_members g2 on g.geographical_area_sid = g2.parent_sid
        group by g.geographical_area_sid, g.geographical_area_id, g.description, g.area_type
        order by 2;
        """
        d = Database()
        rows = d.run_query(sql)
        self.all_geographies = []
        g.all_geographies_dict = {}
        for row in rows:
            geographical_area = GeographicalArea2()
            geographical_area.geographical_area_sid = row[0]
            geographical_area.geographical_area_id = row[1]
            geographical_area.description = row[2]
            geographical_area.area_type = row[3]
            geographical_area.members = row[4]
            geographical_area.get_csv_string()

            self.all_geographies.append(geographical_area)
            g.all_geographies_dict[geographical_area.geographical_area_sid] = geographical_area

        self.end_timer("Getting all geographical areas for CSV export")

    def write_all_geographies(self):
        self.start_timer("Writing all geographical areas for CSV export")
        self.geography_csv_file = open(self.geography_csv_filepath, "w+")
        self.geography_csv_file.write('"geographical_area_id","description","area_type","members"' + CommonString.line_feed)
        for geographical_area in self.all_geographies:
            self.geography_csv_file.write(geographical_area.csv_string)

        self.end_timer("Getting and writing all geographical areas for CSV export")
        self.geography_csv_file.close()

    def write_commodities_csv(self):
        self.commodity_csv_file = open(self.commodity_csv_filepath, "w+")
        self.commodity_csv_file.write(
            '"commodity__sid","commodity__code","productline__suffix","start__date","end__date","description","indents","entity__type","end__line","commodity__code__pls","hierarchy__of__sids","hierarchy__of__ids"\n'
        )
        for c in g.commodities_dict:
            commodity = g.commodities_dict[c]
            self.commodity_csv_file.write(commodity.commodity_record_for_csv + "\n")

        self.commodity_csv_file.close()

    def zip_and_upload(self):
        if self.CREATE_ZIP or self.CREATE_7Z:
            print("Zipping file")
            self.aws_path_icl_vme_tuple = Zipper(self.filepath_icl_vme, self.scope, "icl_vme", "ICL VME file").compress()
            self.aws_path_measures_csv_tuple = Zipper(self.measure_csv_filepath, self.scope, "csv", "Measures CSV").compress()
            self.aws_path_commodities_csv_tuple = Zipper(self.commodity_csv_filepath, self.scope, "csv", "Commodities CSV").compress()
            if self.WRITE_ANCILLARY_FILES:
                self.aws_path_mfn_csv_tuple = Zipper(self.mfn_csv_filepath, self.scope, "csv", "Third country duty CSV").compress()
                self.aws_path_supplementary_units_csv_tuple = Zipper(self.supplementary_units_csv_filepath, self.scope, "csv", "Supplementary units CSV").compress()
                self.aws_path_footnotes_csv_tuple = Zipper(self.footnote_csv_filepath, self.scope, "csv", "Footnotes CSV").compress()
                self.aws_path_certificates_csv_tuple = Zipper(self.certificate_csv_filepath, self.scope, "csv", "Certificates CSV").compress()
                self.aws_path_quotas_csv_tuple = Zipper(self.quota_csv_filepath, self.scope, "csv", "Quotas CSV").compress()
                self.aws_path_geographical_areas_csv_tuple = Zipper(self.geography_csv_filepath, self.scope, "csv", "Geographical areas CSV").compress()
                self.aws_path_measure_types_csv_tuple = Zipper(self.measure_type_csv_filepath, self.scope, "csv", "Geographical areas CSV").compress()
                self.aws_path_additional_codes_csv_tuple = Zipper(self.additional_code_csv_filepath, self.scope, "csv", "Additional codes CSV").compress()
                self.aws_path_mfns_csv_tuple = Zipper(self.mfn_csv_filepath, self.scope, "csv", "Additional codes CSV").compress()
                self.aws_path_supplementary_units_csv_tuple = Zipper(self.supplementary_units_csv_filepath, self.scope, "csv", "Additional codes CSV").compress()
            else:
                self.aws_path_mfn_csv_tuple = ("n/a", "n/a")
                self.aws_path_supplementary_units_csv_tuple = ("n/a", "n/a")
                self.aws_path_footnotes_csv_tuple = ("n/a", "n/a")
                self.aws_path_certificates_csv_tuple = ("n/a", "n/a")
                self.aws_path_quotas_csv_tuple = ("n/a", "n/a")
                self.aws_path_geographical_areas_csv_tuple = ("n/a", "n/a")
                self.aws_path_measure_types_csv_tuple = ("n/a", "n/a")
                self.aws_path_additional_codes_csv_tuple = ("n/a", "n/a")
                self.aws_path_mfns_csv_tuple = ("n/a", "n/a")
                self.aws_path_supplementary_units_csv_tuple = ("n/a", "n/a")

        # Delta description files
        self.aws_path_commodities_delta_tuple = Zipper(self.delta.commodities_filename, self.scope, "delta", "Changes to commodity codes").compress()
        self.aws_path_measures_delta_tuple = Zipper(self.delta.measures_filename, self.scope, "delta", "Changes to measures").compress()
        print("Zipping complete")

    def create_email_message(self):
        if self.SEND_MAIL == 0 or self.CREATE_7Z == 0 or self.CREATE_ZIP == 0 or self.WRITE_TO_AWS == 0:
            return

        self.html_content = """
        <p style="color:#000">Dear all,</p>
        <p style="color:#000">The following data files are available for download, representing tariff data for <b>{snapshot_date}</b>:</p>
        <p style="color:#000">Changes in this issue are as listed in the relevant links, as follows:</p>

        <table cellspacing="0">
            <tr valign="top">
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">Description</th>
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">File</th>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Commodity changes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{commodity_changes}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Measure changes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{measure_changes}</td>
            </tr>
        </table>

        <p style="color:#000">Two additional files are attached to this email, as follows:</p>
        <ul style="color:#000;">
            <li style="color:#000;">Documentation on the attached CSV formats</li>
            <li style="color:#000;">ASCII file and CDS measure type correlation table</li>
        </ul>

        <p style="color:#000"><b>Files compressed using ZIP compression</b>:</p>
        <table cellspacing="0">
            <tr valign="top">
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">Description</th>
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">File</th>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Electronic Tariff File (ICL VME format)</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{icl_vme_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Measures, as applied to commodity codes (CSV)</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{measures_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Commodities</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{commodities_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Footnotes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{footnotes_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Certificates</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{certificates_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Quotas</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{quotas_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Geographical areas</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{geographical_areas_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Measure types</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{measure_types_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Additional codes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{additional_codes_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;"> MFN rates only</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{mfns_zip}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Supplementary units only</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{supplementary_units_zip}</td>
            </tr>
        </table>

        <br><br>

        <p style="color:#000"><b>Files compressed using 7z compression</b>:</p>

        <table cellspacing="0">
            <tr valign="top">
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">Description</th>
                <th style="text-align:left;padding:2px 5px;border:1px #CCC solid;background-color:#CCC;color:#000;">File</th>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Electronic Tariff File (ICL VME format)</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{icl_vme_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Measures, as applied to commodity codes (CSV)</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{measures_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Commodities</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{commodities_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Footnotes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{footnotes_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Certificates</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{certificates_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Quotas</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{quotas_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Geographical areas</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{geographical_areas_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Measure types</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{measure_types_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Additional codes</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{additional_codes_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">MFN rates only</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{mfns_7z}</td>
            </tr>
            <tr valign="top">
                <td style="padding:2px 5px;border:1px #CCC solid;background-color:#fafafa;color:#000;">Supplementary units only</td>
                <td style="padding:2px 5px;border:1px #CCC solid;color:#000;">{supplementary_units_7z}</td>
            </tr>
        </table>

        <p style="color:#000">Thank you,</p>
        <p style="color:#000">The Online Tariff Team.</p>""".format(
            snapshot_date=g.SNAPSHOT_DATE,
            commodity_changes=self.bucket_url + self.aws_path_commodities_delta_tuple[1],
            measure_changes=self.bucket_url + self.aws_path_measures_delta_tuple[1],
            icl_vme_zip=self.bucket_url + self.aws_path_icl_vme_tuple[1],
            icl_vme_7z=self.bucket_url + self.aws_path_icl_vme_tuple[0],
            measures_zip=self.bucket_url + self.aws_path_measures_csv_tuple[1],
            measures_7z=self.bucket_url + self.aws_path_measures_csv_tuple[0],
            commodities_zip=self.bucket_url + self.aws_path_commodities_csv_tuple[1],
            commodities_7z=self.bucket_url + self.aws_path_commodities_csv_tuple[0],
            footnotes_zip=self.bucket_url + self.aws_path_footnotes_csv_tuple[1],
            footnotes_7z=self.bucket_url + self.aws_path_footnotes_csv_tuple[0],
            certificates_zip=self.bucket_url + self.aws_path_certificates_csv_tuple[1],
            certificates_7z=self.bucket_url + self.aws_path_certificates_csv_tuple[0],
            quotas_zip=self.bucket_url + self.aws_path_quotas_csv_tuple[1],
            quotas_7z=self.bucket_url + self.aws_path_quotas_csv_tuple[0],
            geographical_areas_zip=self.bucket_url + self.aws_path_geographical_areas_csv_tuple[1],
            geographical_areas_7z=self.bucket_url + self.aws_path_geographical_areas_csv_tuple[0],
            measure_types_zip=self.bucket_url + self.aws_path_measure_types_csv_tuple[1],
            measure_types_7z=self.bucket_url + self.aws_path_measure_types_csv_tuple[0],
            additional_codes_zip=self.bucket_url + self.aws_path_additional_codes_csv_tuple[1],
            additional_codes_7z=self.bucket_url + self.aws_path_additional_codes_csv_tuple[0],
            mfns_zip=self.bucket_url + self.aws_path_mfns_csv_tuple[1],
            mfns_7z=self.bucket_url + self.aws_path_mfns_csv_tuple[0],
            supplementary_units_zip=self.bucket_url + self.aws_path_supplementary_units_csv_tuple[1],
            supplementary_units_7z=self.bucket_url + self.aws_path_supplementary_units_csv_tuple[0]
        )

    def send_email_message(self):
        if self.SEND_MAIL == 0 or self.CREATE_7Z == 0 or self.CREATE_ZIP == 0 or self.WRITE_TO_AWS == 0:
            return
        subject = "Issue of updated HMRC Electronic Tariff File for " + g.SNAPSHOT_DATE
        attachment_list = [
            self.documentation_file,
            self.correlation_file
        ]
        s = SendgridMailer(subject, self.html_content, attachment_list)
        s.send()

    def create_delta(self):
        print("Creating delta")
        g.change_date = g.SNAPSHOT_DATE
        g.change_period = "week"
        self.delta = Delta(self.use_materialized_views)
        print("Delta complete")
