import sys
import classes.globals as g
from classes_gen.database import Database


class GeographicalArea(object):
    def __init__(self, taric_area, chief_area, suppress):
        
        self.taric_area = taric_area
        self.chief_area = chief_area
        self.suppress = suppress
        self.members = []
        
        if self.taric_area == "2020":
            a = 1
        
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
            order by 1;
            """
            d = Database()
            rows = d.run_query(sql)
            for row in rows:
                self.members.append(row[0])
        else:
            self.has_members = False
