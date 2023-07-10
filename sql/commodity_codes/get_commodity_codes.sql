/* This is not complete */
with cer as (
    select distinct on (goods_nomenclature_sid)
    goods_nomenclature_sid, goods_nomenclature_item_id, productline_suffix,
    number_indents, description,
    validity_start_date, validity_end_date,
    description_start_date, description_end_date,
    indent_start_date, indent_end_date
    from utils.materialized_commodities_new
    where validity_start_date <= %s
    and validity_end_date >= %s
    and indent_start_date <= %s
    and indent_end_date >= %s
    and description_start_date <= %s
    and description_end_date >= %s
    and goods_nomenclature_item_id >= %s
    and goods_nomenclature_item_id <= %s
    order by goods_nomenclature_sid, description_start_date desc, indent_start_date desc
) select * from cer
where cer.goods_nomenclature_item_id not in (select goods_nomenclature_item_id from hidden_goods_nomenclatures)
order by goods_nomenclature_item_id, productline_suffix