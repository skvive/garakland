import os
import unittest

os.environ["DATABASE_URL"] = "postgresql://u:p@localhost/db"
import db_adapter as d  # noqa: E402


class AdaptSqlTest(unittest.TestCase):
    def test_camel_columns_quoted(self):
        sql = (
            "SELECT s.coordinateStatus FROM stores WHERE coordinateStatus=\"verified\" "
            "AND s.blogUrl != \"\""
        )
        out = d._adapt_sql(sql)
        self.assertIn('s."coordinateStatus"', out)
        self.assertIn('"coordinateStatus"=\'verified\'', out)
        self.assertIn('"blogUrl"', out)


if __name__ == "__main__":
    unittest.main()
