with measures as (
SELECT m.measure_sid,
    m.additional_code_sid,
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
    m.additional_code_sid,
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
),

additional_codes as (
SELECT DISTINCT ON (ac.additional_code_type_id, ac.additional_code) ac.additional_code_type_id::text || ac.additional_code::text AS code,
    acd.description,
    ac.validity_start_date,
    ac.validity_end_date,
    ac.additional_code_type_id,
    ac.additional_code,
    ac.additional_code_sid,
    actd.description as additional_code_type_description
   FROM additional_codes ac,
    additional_code_description_periods acdp,
    additional_code_descriptions acd,
    additional_code_type_descriptions actd
	WHERE ac.additional_code_sid = acd.additional_code_sid
	AND ac.additional_code_sid = acdp.additional_code_sid
	and ac.additional_code_type_id = actd.additional_code_type_id
  ORDER BY ac.additional_code_type_id, ac.additional_code, acdp.validity_start_date DESC
)
select distinct ac.code, ac.description, ac.validity_start_date, ac.validity_end_date, ac.additional_code_type_description
from additional_codes ac, measures m
where ac.additional_code_sid = m.additional_code_sid
and m.validity_start_date < %s
and (m.validity_end_date is null or m.validity_end_date::date >= %s)
order by 1;