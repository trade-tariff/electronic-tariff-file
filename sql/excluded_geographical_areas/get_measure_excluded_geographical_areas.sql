with measures as (
SELECT m.measure_sid,
    m.goods_nomenclature_item_id,
    m.goods_nomenclature_sid,
    to_char(m.validity_start_date, 'YYYY-MM-DD'::text) AS validity_start_date,
        CASE
            WHEN m.validity_end_date IS NOT NULL THEN to_char(m.validity_end_date, 'YYYY-MM-DD'::text)
            WHEN mr.effective_end_date IS NOT NULL THEN to_char(mr.effective_end_date, 'YYYY-MM-DD'::text)
            WHEN mr.validity_end_date IS NOT NULL THEN to_char(mr.validity_end_date, 'YYYY-MM-DD'::text)
            ELSE NULL::text
        END AS validity_end_date
   FROM measures m,
    modification_regulations mr
  WHERE m.measure_generating_regulation_role = 4 AND m.measure_generating_regulation_id::text = mr.modification_regulation_id::text AND m.measure_generating_regulation_role = mr.modification_regulation_role AND mr.approved_flag IS NOT FALSE
UNION
 SELECT m.measure_sid,
    m.goods_nomenclature_item_id,
    m.goods_nomenclature_sid,
    to_char(m.validity_start_date, 'YYYY-MM-DD'::text) AS validity_start_date,
        CASE
            WHEN m.validity_end_date IS NOT NULL THEN to_char(m.validity_end_date, 'YYYY-MM-DD'::text)
            WHEN br.effective_end_date IS NOT NULL THEN to_char(br.effective_end_date, 'YYYY-MM-DD'::text)
            WHEN br.validity_end_date IS NOT NULL THEN to_char(br.validity_end_date, 'YYYY-MM-DD'::text)
            ELSE NULL::text
        END AS validity_end_date
   FROM measures m,
    base_regulations br
  WHERE m.measure_generating_regulation_role <> 4 AND m.measure_generating_regulation_id::text = br.base_regulation_id::text AND m.measure_generating_regulation_role = br.base_regulation_role AND br.approved_flag IS NOT FALSE
)
select mega.measure_sid, mega.excluded_geographical_area, mega.geographical_area_sid
from measure_excluded_geographical_areas mega, measures m,
goods_nomenclatures gn
where m.measure_sid = mega.measure_sid
and m.goods_nomenclature_sid = gn.goods_nomenclature_sid
and m.validity_start_date <= %s
and (m.validity_end_date is null or m.validity_end_date > %s)
and gn.validity_start_date <= %s
and (gn.validity_end_date is null or gn.validity_end_date > %s)
and mega.excluded_geographical_area != 'EU'
order by mega.measure_sid, mega.excluded_geographical_area;
