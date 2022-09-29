from classes_gen.spv.spv_measure import SPVMeasure
from classes_gen.spv.spv_measure_component import SPVMeasureComponent
from classes_gen.database import Database


class SPVHandler(object):
    def __init__(self, snapshot_date):
        self.measures = []
        self.measure_components = []
        self.snapshot_date = snapshot_date
        self.get_measures()
        self.get_measure_components()

    def get_measures(self):
        sql = """
        select m.measure_sid, m.goods_nomenclature_item_id, m.goods_nomenclature_sid
        from utils.measures_real_end_dates m
        where m.measure_type_id = '488'
        and m.validity_start_date::date <= %s
        and (m.validity_end_date::date >= %s or m.validity_end_date is null)
        order by goods_nomenclature_item_id;
        """

        d = Database()
        params = [
            self.snapshot_date,
            self.snapshot_date
        ]
        rows = d.run_query(sql, params)
        for row in rows:
            measure = SPVMeasure(row)
            self.measures.append(measure)
        a = 1

    def get_measure_components(self):
        sql = """
        select mc.measure_sid, mc.duty_expression_id, mc.duty_amount, mc.monetary_unit_code,
        mc.measurement_unit_code, mc.measurement_unit_qualifier_code
        from measure_components mc, utils.measures_real_end_dates m
        where m.measure_sid = mc.measure_sid
        and m.measure_type_id = '488'
        and m.validity_start_date::date <= %s
        and (m.validity_end_date::date >= %s or m.validity_end_date is null)
        order by measure_sid, duty_expression_id
        """

        d = Database()
        params = [
            self.snapshot_date,
            self.snapshot_date
        ]
        rows = d.run_query(sql, params)
        for row in rows:
            measure_component = SPVMeasureComponent(row)
            self.measure_components.append(measure_component)
        a = 1
