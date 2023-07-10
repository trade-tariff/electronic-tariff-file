with measures as (
SELECT m.measure_sid,
    m.goods_nomenclature_sid,
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
    m.goods_nomenclature_sid,
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
), footnotes AS (
  SELECT
    fd1.footnote_type_id,
    fd1.footnote_id,
    fd1.footnote_type_id || fd1.footnote_id AS code,
    fd1.description,
    f1.validity_start_date,
    f1.validity_end_date
  FROM
    footnote_descriptions fd1,
    footnotes f1
  WHERE
    fd1.footnote_id = f1.footnote_id
    AND fd1.footnote_type_id = f1.footnote_type_id
    AND (fd1.footnote_description_period_sid IN (
        SELECT
          max(ft2.footnote_description_period_sid) AS max
      FROM
        footnote_descriptions ft2
      WHERE
        fd1.footnote_type_id = ft2.footnote_type_id
        AND fd1.footnote_id = ft2.footnote_id)))
SELECT DISTINCT
  f.code,
  f.description,
  f.validity_start_date,
  f.validity_end_date,
  'measure' AS footnote_class
FROM
  footnotes f,
  footnote_association_measures fam,
  measures m,
  goods_nomenclatures gn
WHERE
  gn.goods_nomenclature_sid = m.goods_nomenclature_sid
  AND f.footnote_id = fam.footnote_id
  AND f.footnote_type_id = fam.footnote_type_id
  AND fam.measure_sid = m.measure_sid
  AND m.validity_start_date <= %s
  AND (m.validity_end_date IS NULL OR m.validity_end_date >= %s)
  AND gn.validity_start_date <= %s
  AND (gn.validity_end_date IS NULL OR gn.validity_end_date >= %s)
  AND f.validity_start_date <= %s
  AND (f.validity_end_date IS NULL OR f.validity_end_date >= %s)
UNION
SELECT DISTINCT
  f.code,
  f.description,
  f.validity_start_date,
  f.validity_end_date,
  'commodity' AS footnote_class
FROM
  footnotes f,
  footnote_association_goods_nomenclatures fagn,
  goods_nomenclatures gn
WHERE
  f.footnote_id = fagn.footnote_id
  AND f.footnote_type_id = fagn.footnote_type
  AND fagn.goods_nomenclature_sid = gn.goods_nomenclature_sid
  AND gn.validity_start_date <= %s
  AND (gn.validity_end_date IS NULL OR gn.validity_end_date >= %s)
  AND f.validity_start_date <= %s
  AND (f.validity_end_date IS NULL OR f.validity_end_date >= %s)
ORDER BY 1;
