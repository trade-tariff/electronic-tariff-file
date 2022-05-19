import sys
import classes.globals as g
from classes_gen.database import Database
from classes.functions import functions as f
from classes.enums import CommonString


class GeographicalArea(object):
    def __init__(self, taric_area, chief_area, suppress):

        self.taric_area = taric_area
        self.chief_area = chief_area
        self.suppress = suppress
        self.members = []

        if self.chief_area == "expand":
            self.has_members = True
            # Expand into members
            sql = """
            select ga_child.geographical_area_id from geographical_area_memberships gam, geographical_areas ga_parent, geographical_areas ga_child
            where ga_parent.geographical_area_sid = gam.geographical_area_group_sid
            and ga_child.geographical_area_sid = gam.geographical_area_sid
            and ga_parent.geographical_area_id = '""" + self.taric_area + """'
            and gam.validity_start_date < '""" + g.app.SNAPSHOT_DATE + """'
            and (gam.validity_end_date is null or gam.validity_end_date > '""" + g.app.SNAPSHOT_DATE + """')
            and ga_child.geographical_area_id != 'EU'
            order by 1;
            """
            d = Database()
            rows = d.run_query(sql)
            for row in rows:
                self.members.append(row[0])
        else:
            self.has_members = False


class GeographicalArea2(object):
    def get_csv_string(self):
        self.format_description_for_csv()
        s = ""
        s += CommonString.quote_char + f.null_to_string(self.geographical_area_id) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.description) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.area_type) + CommonString.quote_char + CommonString.comma
        s += CommonString.quote_char + f.null_to_string(self.members) + CommonString.quote_char
        s += CommonString.line_feed
        self.csv_string = s

    def format_description_for_csv(self):
        if self.description is None:
            self.description = ""
        self.description = self.description.replace('"', "'")
        self.description = self.description.replace('\n', " ")
        self.description = self.description.replace('\r', " ")
        self.description = self.description.replace('  ', " ")
