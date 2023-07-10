import os


class SqlQuery(object):
    def __init__(self, folder, filename):
        self.filename = os.path.join(os.getcwd(), "sql", folder, filename)
        f = open(self.filename, "r")
        self.sql = f.read()
        self.sql = self.sql.replace("\n", " ")
        f.close()
