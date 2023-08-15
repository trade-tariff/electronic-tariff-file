WITH commodities AS (
    SELECT DISTINCT ON (goods_nomenclature_sid)
        gn.goods_nomenclature_sid,
        gn.goods_nomenclature_item_id,
        gn.producline_suffix AS productline_suffix,
        gni.number_indents,
        gnd.description,
        gn.validity_start_date,
        COALESCE(gn.validity_end_date, '2999-12-31'::date::timestamp without time zone) AS validity_end_date,
        gndp.validity_start_date AS description_start_date,
        COALESCE(gndp.validity_end_date, '2999-12-31'::date::timestamp without time zone) AS description_end_date,
        gni.validity_start_date AS indent_start_date,
        COALESCE(gni.validity_end_date, '2999-12-31'::date::timestamp without time zone) AS indent_end_date
    FROM goods_nomenclatures gn
    JOIN goods_nomenclature_description_periods gndp ON gndp.goods_nomenclature_sid = gn.goods_nomenclature_sid
    JOIN goods_nomenclature_descriptions gnd ON gndp.goods_nomenclature_description_period_sid = gnd.goods_nomenclature_description_period_sid
    JOIN goods_nomenclature_indents gni ON gn.goods_nomenclature_sid = gni.goods_nomenclature_sid
    WHERE
        gnd.description IS NOT NULL
        AND gn.validity_start_date <= %s
        AND (gn.validity_end_date IS NULL OR gn.validity_end_date >= %s)
        AND gni.validity_start_date <= %s
        AND (gni.validity_end_date IS NULL OR gni.validity_end_date >= %s)
        AND gndp.validity_start_date <= %s
        AND (gndp.validity_end_date IS NULL OR gndp.validity_end_date >= %s)
        AND gn.goods_nomenclature_item_id >= %s
        AND gn.goods_nomenclature_item_id <= %s
    ORDER BY
        goods_nomenclature_sid,
        description_start_date DESC,
        indent_start_date DESC
)

SELECT *
FROM commodities
WHERE commodities.goods_nomenclature_item_id NOT IN (
    SELECT goods_nomenclature_item_id
    FROM hidden_goods_nomenclatures
)
ORDER BY
    goods_nomenclature_item_id,
    productline_suffix;
