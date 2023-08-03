with measures as (
SELECT m.measure_sid,
    m.ordernumber,
    m.geographical_area_id,
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
    m.ordernumber,
    m.geographical_area_id,
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
SELECT
    qon.quota_order_number_sid,
    qon.quota_order_number_id,
    qd.validity_start_date,
    qd.validity_end_date,
    qd.initial_volume,
    qd.measurement_unit_code || ' ' || coalesce(qd.measurement_unit_qualifier_code, '') AS unit,
    qd.critical_state,
    qd.critical_threshold,
    'First Come First Served' AS quota_type,
    string_agg(DISTINCT qono.geographical_area_id, '|' ORDER BY qono.geographical_area_id) AS origins
FROM
    quota_order_numbers qon,
    quota_definitions qd,
    quota_order_number_origins qono
WHERE
    qd.quota_order_number_sid = qon.quota_order_number_sid
    AND qon.quota_order_number_sid = qono.quota_order_number_sid
    AND left(qon.quota_order_number_id, 2) = %s
    AND qon.validity_start_date <= %s
    AND (qon.validity_end_date IS NULL OR qon.validity_end_date >= %s)
    AND qd.validity_start_date <= %s
    AND (qd.validity_end_date IS NULL OR qd.validity_end_date >= %s)
GROUP BY
    qon.quota_order_number_sid,
    qon.quota_order_number_id,
    qd.validity_start_date,
    qd.validity_end_date,
    qd.initial_volume,
    qd.measurement_unit_code,
    qd.measurement_unit_qualifier_code,
    qd.critical_state,
    qd.critical_threshold
UNION
SELECT
    NULL AS quota_order_number_sid,
    m.ordernumber AS quota_order_number_id,
    m.validity_start_date,
    m.validity_end_date,
    NULL AS initial_volume,
    NULL AS unit,
    NULL AS critical_state,
    NULL AS critical_threshold,
    'Licensed' AS quota_type,
    string_agg(DISTINCT m.geographical_area_id, '|' ORDER BY m.geographical_area_id) AS origins
FROM
    measures m
WHERE
    left(ordernumber, 3) = %s
    AND m.validity_start_date <= %s
    AND (m.validity_end_date IS NULL OR m.validity_end_date >= %s)
GROUP BY
    m.ordernumber,
    m.validity_start_date,
    m.validity_end_date
ORDER BY 2
