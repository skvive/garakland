"""Postgres SQL conversion tests without mutating process-wide DB settings."""
import unittest
from unittest.mock import patch
import db_adapter as d


class AdaptSqlTest(unittest.TestCase):
    def test_query_offers_join(self):
        # Do not set os.environ or db_adapter.DATABASE_URL at module import;
        # unittest discover imports all files into the same test process.
        with patch.object(d, "DATABASE_URL", "postgresql://u:p@localhost/db"):
            sql = (
                "SELECT o.*,s.coordinateStatus FROM v5_offers o JOIN stores s ON s.id=o.shop_id "
                "ORDER BY o.created_at DESC"
            )
            out = d._adapt_sql(sql)
            self.assertIn('s."coordinateStatus"', out)
            sql = (
                'SELECT s.coordinateStatus FROM stores WHERE coordinateStatus="verified" '
                'AND s.blogUrl != ""'
            )
            out = d._adapt_sql(sql)
            self.assertIn('s."coordinateStatus"', out)
            self.assertIn('\\\"coordinateStatus\\\"', "") if False else None
            self.assertIn('\"coordinateStatus\"=\'verified\'', out)
            self.assertIn('\"blogUrl\"', out)


if __name__ == "__main__":
    unittest.main()
