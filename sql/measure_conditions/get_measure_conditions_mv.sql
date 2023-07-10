select mc.measure_sid, mc.measure_condition_sid, mc.condition_code, mc.component_sequence_number,
mc.condition_duty_amount, mc.condition_monetary_unit_code, mc.condition_measurement_unit_code,
mc.condition_measurement_unit_qualifier_code, mc.action_code, mc.certificate_type_code,
mc.certificate_code
from measure_conditions mc, utils.materialized_measures_real_end_dates m, goods_nomenclatures gn
where m.measure_sid = mc.measure_sid
and m.goods_nomenclature_sid = gn.goods_nomenclature_sid
and m.validity_start_date <= %s
and (m.validity_end_date >= %s or m.validity_end_date is null)
and gn.validity_start_date <= %s
and (gn.validity_end_date >= %s or gn.validity_end_date is null)
and m.goods_nomenclature_item_id >= %s
and m.goods_nomenclature_item_id <= %s
and m.goods_nomenclature_item_id not in
(select goods_nomenclature_item_id from hidden_goods_nomenclatures)