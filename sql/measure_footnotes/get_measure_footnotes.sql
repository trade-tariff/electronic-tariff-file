WITH measures AS (
    SELECT
        m.measure_sid,
        m.goods_nomenclature_sid,
        m.goods_nomenclature_item_id,
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
        m.goods_nomenclature_item_id,
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
)
SELECT
    m.measure_sid,
    fam.footnote_type_id || fam.footnote_id AS footnote
FROM
    footnote_association_measures fam,
    measures m,
    goods_nomenclatures gn
WHERE
    fam.measure_sid = m.measure_sid
    AND m.validity_start_date <= %s
    AND m.goods_nomenclature_sid = gn.goods_nomenclature_sid
    AND (m.validity_end_date IS NULL
        OR m.validity_end_date::date > %s)
    AND gn.validity_start_date <= %s
    AND (gn.validity_end_date IS NULL
        OR gn.validity_end_date::date > %s)
    AND m.goods_nomenclature_item_id >= %s
    AND m.goods_nomenclature_item_id <= %s
ORDER BY
    m.measure_sid,
    fam.footnote_type_id,
    fam.footnote_id
