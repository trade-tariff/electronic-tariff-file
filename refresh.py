import classes.globals as g
from classes_gen.database import Database


sql = "REFRESH MATERIALIZED VIEW utils.materialized_measures_real_end_dates"
d = Database()
d.run_query(sql)
