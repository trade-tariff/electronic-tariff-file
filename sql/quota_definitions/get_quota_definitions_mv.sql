SELECT
    qon.quota_order_number_sid,
    qon.quota_order_number_id,
    qd.validity_start_date::date,
    qd.validity_end_date::date,
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
    m.validity_start_date::date,
    m.validity_end_date::date,
    NULL AS initial_volume,
    NULL AS unit,
    NULL AS critical_state,
    NULL AS critical_threshold,
    'Licensed' AS quota_type,
    string_agg(DISTINCT m.geographical_area_id, '|' ORDER BY m.geographical_area_id) AS origins
FROM
    utils.materialized_measures_real_end_dates m
WHERE
    left(ordernumber, 3) = %s
    AND m.validity_start_date <= %s
    AND (m.validity_end_date IS NULL OR m.validity_end_date > %s)
GROUP BY
    m.ordernumber,
    m.validity_start_date,
    m.validity_end_date
ORDER BY 2
