select distinct ac.code, ac.description, ac.validity_start_date, ac.validity_end_date, acd.description as additional_code_description
from utils.additional_codes ac, utils.materialized_measures_real_end_dates m, additional_code_type_descriptions acd
where ac.additional_code_type_id = m.additional_code_type_id
and ac.additional_code = m.additional_code_id
and m.validity_start_date <= %s
and (m.validity_end_date is null or m.validity_end_date::date >= %s)
and ac.additional_code_type_id = acd.additional_code_type_id
order by 1;
