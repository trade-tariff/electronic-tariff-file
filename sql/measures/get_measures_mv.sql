select measure_sid, m.goods_nomenclature_item_id, geographical_area_id,
m.measure_type_id, ordernumber, additional_code, m.goods_nomenclature_sid,
m.validity_start_date::date, m.validity_end_date::date,
case
    when m.measure_type_id in ('103', '105') then 1
    when m.measure_type_id in ('305') then 2
    when m.measure_type_id in ('306') then 3
    when m.measure_type_id in ('142', '145') then 4
    when m.measure_type_id in ('122', '123', '143', '146') then 5
    when m.measure_type_id in ('112', '115', '117', '119') then 6
    when m.measure_type_id in ('551', '552', '553', '554') then 7
    when m.measure_type_id in ('109', '110') then 8
    else  99
end as measure_priority, mt.measure_component_applicable_code, mt.trade_movement_code,
mtd.description as measure_type_description, m.reduction_indicator,
m.geographical_area_sid, m.operation_date
from utils.materialized_measures_real_end_dates m, measure_types mt, measure_type_descriptions mtd, goods_nomenclatures gn
where m.measure_type_id = mt.measure_type_id
and m.goods_nomenclature_sid = gn.goods_nomenclature_sid
and m.measure_type_id = mtd.measure_type_id
and m.validity_start_date <= %s
and (m.validity_end_date >= %s or m.validity_end_date is null)
and gn.validity_start_date <= %s
and (gn.validity_end_date >= %s or gn.validity_end_date is null)
and m.goods_nomenclature_item_id >= %s
and m.goods_nomenclature_item_id <= %s
order by m.goods_nomenclature_item_id, measure_priority, m.measure_type_id, m.additional_code, m.ordernumber
