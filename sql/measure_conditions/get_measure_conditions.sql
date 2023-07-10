with measures as (
SELECT m.measure_sid,
    m.goods_nomenclature_sid,
    m.goods_nomenclature_item_id,
    m.validity_start_date,
        CASE
            WHEN m.validity_end_date IS NOT NULL THEN m.validity_end_date
            WHEN mr.effective_end_date IS NOT NULL THEN mr.effective_end_date
            WHEN mr.validity_end_date IS NOT NULL THEN mr.validity_end_date
            ELSE NULL
        END AS validity_end_date
   FROM measures m,
    modification_regulations mr
  WHERE m.measure_generating_regulation_role = 4
  AND m.measure_generating_regulation_id = mr.modification_regulation_id
  AND m.measure_generating_regulation_role = mr.modification_regulation_role
  AND mr.approved_flag IS NOT FALSE
UNION
 SELECT m.measure_sid,
    m.goods_nomenclature_sid,
    m.goods_nomenclature_item_id,
    m.validity_start_date,
        CASE
            WHEN m.validity_end_date IS NOT NULL THEN m.validity_end_date
            WHEN br.effective_end_date IS NOT NULL THEN br.effective_end_date
            WHEN br.validity_end_date IS NOT NULL THEN br.validity_end_date
            ELSE NULL
        END AS validity_end_date
   FROM measures m,
    base_regulations br
  WHERE m.measure_generating_regulation_role <> 4
  AND m.measure_generating_regulation_id = br.base_regulation_id
  AND m.measure_generating_regulation_role = br.base_regulation_role
  AND br.approved_flag IS NOT FALSE
)
select mc.measure_sid, mc.measure_condition_sid, mc.condition_code, mc.component_sequence_number,
mc.condition_duty_amount, mc.condition_monetary_unit_code, mc.condition_measurement_unit_code,
mc.condition_measurement_unit_qualifier_code, mc.action_code, mc.certificate_type_code,
mc.certificate_code
from measure_conditions mc, measures m, goods_nomenclatures gn
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