SELECT
    ordernumber,
    string_agg(DISTINCT m.goods_nomenclature_item_id, '|' ORDER BY m.goods_nomenclature_item_id)
FROM
    utils.materialized_measures_real_end_dates m, goods_nomenclatures gn
WHERE
    m.goods_nomenclature_sid = gn.goods_nomenclature_sid
    AND left(m.ordernumber, 2) = %s
    AND m.validity_start_date <= %s
    AND (m.validity_end_date IS NULL OR m.validity_end_date >= %s)
    AND gn.validity_start_date <= %s
    AND (gn.validity_end_date IS NULL OR gn.validity_end_date >= %s)
GROUP BY
    ordernumber
ORDER BY
    ordernumber
