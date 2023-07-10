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
        END AS validity_end_date,
        m.geographical_area_id,
        m.geographical_area_sid,
        m.measure_type_id,
        m.ordernumber,
(m.additional_code_type_id || m.additional_code_id) AS additional_code,
        m.reduction_indicator,
        m.operation_date
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
        END AS validity_end_date,
        m.geographical_area_id,
        m.geographical_area_sid,
        m.measure_type_id,
        m.ordernumber,
(m.additional_code_type_id || m.additional_code_id) AS additional_code,
        m.reduction_indicator,
        m.operation_date
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
    m.goods_nomenclature_item_id,
    m.geographical_area_id,
    m.measure_type_id,
    m.ordernumber,
    m.additional_code,
    m.goods_nomenclature_sid,
    m.validity_start_date,
    m.validity_end_date,
    CASE WHEN m.measure_type_id IN ('103', '105') THEN
        1
    WHEN m.measure_type_id IN ('305') THEN
        2
    WHEN m.measure_type_id IN ('306') THEN
        3
    WHEN m.measure_type_id IN ('142', '145') THEN
        4
    WHEN m.measure_type_id IN ('122', '123', '143', '146') THEN
        5
    WHEN m.measure_type_id IN ('112', '115', '117', '119') THEN
        6
    WHEN m.measure_type_id IN ('551', '552', '553', '554') THEN
        7
    WHEN m.measure_type_id IN ('109', '110') THEN
        8
    ELSE
        99
    END AS measure_priority,
    mt.measure_component_applicable_code,
    mt.trade_movement_code,
    mtd.description AS measure_type_description,
    m.reduction_indicator,
    m.geographical_area_sid,
    m.operation_date
FROM
    measures m,
    measure_types mt,
    measure_type_descriptions mtd,
    goods_nomenclatures gn
WHERE
    m.measure_type_id = mt.measure_type_id
    AND m.goods_nomenclature_sid = gn.goods_nomenclature_sid
    AND m.measure_type_id = mtd.measure_type_id
    AND m.validity_start_date <= %s
    AND (m.validity_end_date >= %s OR m.validity_end_date IS NULL)
    AND gn.validity_start_date <= %s
    AND (gn.validity_end_date >= %s OR gn.validity_end_date IS NULL)
    AND m.goods_nomenclature_item_id >= %s
    AND m.goods_nomenclature_item_id <= %s
ORDER BY
    m.goods_nomenclature_item_id,
    measure_priority,
    m.measure_type_id,
    m.additional_code,
    m.ordernumber
