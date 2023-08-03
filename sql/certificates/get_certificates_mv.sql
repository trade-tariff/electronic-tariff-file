WITH certificates AS (
    SELECT
        cd1.certificate_type_code,
        cd1.certificate_code,
        cd1.certificate_type_code || cd1.certificate_code AS code,
        cd1.description,
        c.validity_start_date,
        c.validity_end_date
    FROM
        certificate_descriptions cd1,
        certificates c
    WHERE
        c.certificate_code = cd1.certificate_code
        AND c.certificate_type_code = cd1.certificate_type_code
        AND (cd1.oid IN (
                SELECT
                    max(cd2.oid) AS max
            FROM
                certificate_descriptions cd2
            WHERE
                cd1.certificate_type_code = cd2.certificate_type_code
                AND cd1.certificate_code = cd2.certificate_code)))
SELECT DISTINCT
    c.code,
    c.description,
    c.validity_start_date,
    c.validity_end_date
FROM
    measure_conditions mc,
    utils.materialized_measures_real_end_dates m,
    certificates c,
    goods_nomenclatures gn
WHERE
    m.measure_sid = mc.measure_sid
    AND m.goods_nomenclature_sid = gn.goods_nomenclature_sid
    AND mc.certificate_type_code = c.certificate_type_code
    AND mc.certificate_code = c.certificate_code
    AND m.validity_start_date <= %s
    AND (m.validity_end_date IS NULL
        OR m.validity_end_date >= %s)
    AND c.validity_start_date <= %s
    AND (c.validity_end_date IS NULL
        OR c.validity_end_date >= %s)
    AND gn.validity_start_date <= %s
    AND (gn.validity_end_date IS NULL
        OR gn.validity_end_date >= %s)
ORDER BY 1
