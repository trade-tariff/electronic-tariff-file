select mtd.measure_type_id, mtd.description, count(m.*)
from measure_types mt, measure_type_descriptions mtd, utils.materialized_measures_real_end_dates m
where mt.measure_type_id = mtd.measure_type_id
and m.measure_type_id = mt.measure_type_id
and m.validity_start_date <= %s
and (m.validity_end_date is null or m.validity_end_date >= %s)
group by mtd.measure_type_id, mtd.description
order by measure_type_id