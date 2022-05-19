import csv
import os
from datetime import datetime, timedelta
from monthdelta import monthdelta
from classes_gen.database import Database
from classes.delta_commodity import DeltaCommodity
from classes.delta_measure import DeltaMeasure
import classes.globals as g


class Delta(object):
    def __init__(self):
        self.get_periods()

        # Commodity changes
        self.delta_commodities = []
        self.get_commodity_change_new()
        self.get_commodity_change_end()

        # Measure changes
        self.delta_measures = []
        self.get_measure_change()

        # Write data
        self.open_delta_file()
        self.write_commodities()
        self.write_measures()
        self.close_delta_file()

    def open_delta_file(self):
        folder = g.app.delta_folder
        self.commodities_filename = os.path.join(folder, "commodities_{}.csv".format(self.to_date_string))
        self.measures_filename = os.path.join(folder, "measures_{}.csv".format(self.to_date_string))

        self.delta_file_commodities = open(self.commodities_filename, "w")
        self.delta_file_measures = open(self.measures_filename, "w")

    def write_commodities(self):
        writer = csv.writer(self.delta_file_commodities, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        fields = [
            "Operation",
            "Commodity code",
            "Product line suffix",
            "Description",
            "Start date",
            "End date"
        ]
        writer.writerow(fields)
        for delta_commodity in self.delta_commodities:
            writer.writerow([
                delta_commodity.operation,
                delta_commodity.goods_nomenclature_item_id,
                delta_commodity.productline_suffix,
                delta_commodity.description,
                delta_commodity.validity_start_date,
                delta_commodity.validity_end_date
            ])

    def write_measures(self):
        writer = csv.writer(self.delta_file_measures, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        fields = [
            "Operation",
            "Commodity code",
            "Geographical area",
            "Measure type",
            "Start date",
            "End date"
        ]
        writer.writerow(fields)
        for delta_measure in self.delta_measures:
            writer.writerow([
                delta_measure.operation,
                delta_measure.goods_nomenclature_item_id,
                delta_measure.geographical_area_id,
                delta_measure.measure_type_description,
                delta_measure.validity_start_date,
                delta_measure.validity_end_date
            ])

    def close_delta_file(self):
        self.delta_file_commodities.close()
        self.delta_file_measures.close()

    def get_periods(self):
        g.app.change_date = g.app.change_date.replace("/", "-")
        g.app.change_date = g.app.change_date.replace(" ", "-")

        self.to_date = datetime.strptime(g.app.change_date, '%Y-%m-%d')
        if (g.app.change_period == "week"):
            self.from_date = self.to_date - timedelta(days=7)
        elif (g.app.change_period == "month"):
            self.from_date = self.to_date - monthdelta(1)
        else:
            self.from_date = self.to_date - timedelta(days=1)

        self.from_date_string = datetime.strftime(self.from_date, '%Y-%m-%d')
        self.to_date_string = datetime.strftime(self.to_date, '%Y-%m-%d')

    def get_commodity_change_new(self):
        sql = """
        with cte as (
            select distinct on (gn.goods_nomenclature_sid)
            gn.goods_nomenclature_item_id, gn.producline_suffix, gnd.description,
            gn.validity_start_date, gn.validity_end_date
            from goods_nomenclatures gn, goods_nomenclature_descriptions gnd
            where gn.goods_nomenclature_sid = gnd.goods_nomenclature_sid
            and validity_start_date >= %s
            and validity_start_date <= %s
            order by gn.goods_nomenclature_sid
        )
        select * from cte order by goods_nomenclature_item_id;
        """
        params = [
            self.from_date,
            self.to_date
        ]
        d = Database()
        rows = d.run_query(sql, params)
        if len(rows) > 0:
            for row in rows:
                delta_commodity = DeltaCommodity(row, "New")
                self.delta_commodities.append(delta_commodity)

    def get_commodity_change_end(self):
        sql = """
        with cte as (
            select distinct on (gn.goods_nomenclature_sid)
            gn.goods_nomenclature_item_id, gn.producline_suffix, gnd.description,
            gn.validity_start_date, gn.validity_end_date
            from goods_nomenclatures gn, goods_nomenclature_descriptions gnd
            where gn.goods_nomenclature_sid = gnd.goods_nomenclature_sid
            and validity_end_date >= %s
            and validity_end_date <= %s
            order by gn.goods_nomenclature_sid
        )
        select * from cte order by goods_nomenclature_item_id;

        """
        params = [
            self.from_date,
            self.to_date
        ]
        d = Database()
        rows = d.run_query(sql, params)
        if len(rows) > 0:
            for row in rows:
                delta_commodity = DeltaCommodity(row, "Close")
                self.delta_commodities.append(delta_commodity)

    def get_measure_change(self):
        sql = """
        select m.goods_nomenclature_item_id,
        m.geographical_area_id, mtd.description as measure_type_description,
        m.validity_start_date, m.validity_end_date
        from utils.materialized_measures_real_end_dates m, measure_type_descriptions mtd
        where m.measure_type_id = mtd.measure_type_id
        and m.validity_start_date >= %s
        and m.validity_start_date <= %s
        order by m.measure_type_id, m.goods_nomenclature_item_id;
        """

        params = [
            self.from_date_string,
            self.to_date_string
        ]

        d = Database()
        rows = d.run_query(sql, params)
        if len(rows) > 0:
            for row in rows:
                delta_measure = DeltaMeasure(row, "New")
                self.delta_measures.append(delta_measure)
