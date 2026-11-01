"""Read-only contract tests for Neon pg8000 connection routing.

No real DB connection or credentials are required. Never log connection URLs.
"""
import unittest
from db_adapter import pg8000_connection_target


class Pg8000ConnectionTargetTests(unittest.TestCase):
    def test_neon_pooler_resolves_direct_host(self):
        url = "postgresql://user:p%40ss@ep-example-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
        target = pg8000_connection_target(url)
        self.assertEqual(target["host"], "ep-example.us-east-2.aws.neon.tech")
        self.assertEqual(target["password"], "p@ss")
        self.assertEqual(target["database"], "neondb")
        self.assertEqual(target["port"], 5432)

    def test_existing_direct_host_is_unchanged(self):
        url = "postgresql://u:p@ep-example.us-east-2.aws.neon.tech/neondb"
        self.assertEqual(pg8000_connection_target(url)["host"], "ep-example.us-east-2.aws.neon.tech")

    def test_non_neon_host_is_not_rewritten(self):
        url = "postgresql://u:p@internal-pooler.db.example.com/application"
        self.assertEqual(pg8000_connection_target(url)["host"], "internal-pooler.db.example.com")

    def test_explicit_direct_override_takes_precedence(self):
        pooled = "postgresql://u:p@ep-pooled-pooler.us-east-2.aws.neon.tech/neondb"
        direct = "postgresql://own:token@ep-custom.us-east-2.aws.neon.tech/production"
        target = pg8000_connection_target(pooled, direct)
        self.assertEqual(target["host"], "ep-custom.us-east-2.aws.neon.tech")
        self.assertEqual(target["database"], "production")
        self.assertEqual(target["user"], "own")

    def test_invalid_scheme_rejected_without_logging_secret(self):
        with self.assertRaises(ValueError):
            pg8000_connection_target("https://u:secret@host.example.com/db")


if __name__ == "__main__":
    unittest.main()
