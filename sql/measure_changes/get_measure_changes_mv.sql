select m.goods_nomenclature_item_id,
m.geographical_area_id, mtd.description as measure_type_description,
m.validity_start_date, m.validity_end_date
from utils.materialized_measures_real_end_dates m, measure_type_descriptions mtd
where m.measure_type_id = mtd.measure_type_id
and m.validity_start_date >= %s
and m.validity_start_date <= %s
order by m.measure_type_id, m.goods_nomenclature_item_id;
