with measures as (
SELECT m.measure_sid,
    m.measure_type_id,
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
  AND m.measure_generating_regulation_id::text = mr.modification_regulation_id::text
  AND m.measure_generating_regulation_role = mr.modification_regulation_role
  AND mr.approved_flag IS NOT FALSE
UNION
 SELECT m.measure_sid,
    m.measure_type_id,
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
  AND m.measure_generating_regulation_id::text = br.base_regulation_id::text
  AND m.measure_generating_regulation_role = br.base_regulation_role
  AND br.approved_flag IS NOT FALSE
)
select distinct mtd.measure_type_id, mtd.description
from measure_types mt, measure_type_descriptions mtd, measures m
where mt.measure_type_id = mtd.measure_type_id
and m.measure_type_id = mt.measure_type_id
and m.validity_start_date <= %s
and (m.validity_end_date is null or m.validity_end_date >= %s)
order by measure_type_id