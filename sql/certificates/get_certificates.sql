WITH measures AS (
    SELECT
        m.measure_sid,
        m.goods_nomenclature_sid,
        m.validity_start_date,
        CASE WHEN m.validity_end_date IS NOT NULL THEN
            m.validity_end_date
        WHEN mr.effective_end_date IS NOT NULL THEN
            mr.effective_end_date
        WHEN mr.validity_end_date IS NOT NULL THEN
            mr.validity_end_date
        ELSE
            NULL
        END AS validity_end_date
    FROM
        measures m,
        modification_regulations mr
    WHERE
        m.measure_generating_regulation_role = 4
        AND m.measure_generating_regulation_id = mr.modification_regulation_id
        AND m.measure_generating_regulation_role = mr.modification_regulation_role
        AND mr.approved_flag IS NOT FALSE
    UNION
    SELECT
        m.measure_sid,
        m.goods_nomenclature_sid,
        m.validity_start_date,
        CASE WHEN m.validity_end_date IS NOT NULL THEN
            m.validity_end_date
        WHEN br.effective_end_date IS NOT NULL THEN
            br.effective_end_date
        WHEN br.validity_end_date IS NOT NULL THEN
            br.validity_end_date
        ELSE
            NULL
        END AS validity_end_date
    FROM
        measures m,
        base_regulations br
    WHERE
        m.measure_generating_regulation_role <> 4
        AND m.measure_generating_regulation_id = br.base_regulation_id
        AND m.measure_generating_regulation_role = br.base_regulation_role
        AND br.approved_flag IS NOT FALSE
),
certificates AS (
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
    measures m,
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
