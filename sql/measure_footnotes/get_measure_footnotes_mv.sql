select mf.measure_sid, mf.footnote
from utils.materialized_measure_footnotes mf, goods_nomenclatures gn
where (mf.validity_end_date is null or mf.validity_end_date::date >= %s)
and (gn.validity_end_date is null or gn.validity_end_date::date >= %s)
and mf.validity_start_date <= %s
and gn.validity_start_date <= %s
and mf.goods_nomenclature_item_id >= %s
and mf.goods_nomenclature_item_id <= %s
and mf.goods_nomenclature_sid = gn.goods_nomenclature_sid
order by mf.measure_sid
