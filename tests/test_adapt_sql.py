import os
import unittest

os.environ["DATABASE_URL"] = "postgresql://u:p@localhost/db"
import db_adapter as d  # noqa: E402


class AdaptSqlTest(unittest.TestCase):
    def test_query_offers_join(self):
        sql = (
            "SELECT o.*,s.coordinateStatus FROM v5_offers o JOIN stores s ON s.id=o.shop_id "
            "ORDER BY o.created_at DESC"
        )
        out = d._adapt_sql(sql)
        self.assertIn('s."coordinateStatus"', out)
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
