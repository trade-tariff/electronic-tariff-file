select mega.measure_sid, mega.excluded_geographical_area, mega.geographical_area_sid
from measure_excluded_geographical_areas mega, utils.materialized_measures_real_end_dates m,
goods_nomenclatures gn
where m.measure_sid = mega.measure_sid
and m.goods_nomenclature_sid = gn.goods_nomenclature_sid
and m.validity_start_date <= %s
and (m.validity_end_date is null or m.validity_end_date > %s)
and gn.validity_start_date <= %s
and (gn.validity_end_date is null or gn.validity_end_date > %s)
and mega.excluded_geographical_area != 'EU'
order by mega.measure_sid, mega.excluded_geographical_area;