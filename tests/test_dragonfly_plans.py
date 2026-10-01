"""Run with: python3 -m unittest discover -s tests (requires jsonschema)."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft7Validator


class DragonflyPlansTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/blueprint.json").read_text())
        Draft7Validator.check_schema(schema)
        cls.validator = Draft7Validator(schema)

    def test_small_plans_are_rejected(self):
        for plan in ("femto", "pico"):
            with self.subTest(plan=plan):
                errors = list(self.validator.iter_errors({
                    "dbServers": [{"name": "cache", "type": "dragonfly", "plan": plan}]
                }))
                self.assertTrue(errors)
                self.assertTrue(all(list(error.path) == ["dbServers", 0, "plan"] for error in errors))

    def test_supported_plans_and_optional_features(self):
        for plan in ("nano", "micro", "small", "medium", "large", "xlarge", "2xlarge", "3xlarge", "4xlarge"):
            with self.subTest(plan=plan):
                self.validator.validate({"dbServers": [{
                    "name": "cache", "type": "dragonfly", "plan": plan,
                    "snapshot": {"enabled": True, "size": "1Gi"},
                    "passwordAuth": {"enabled": True}, "memcached": {"enabled": True},
                    "replicas": 2,
                }]})

    def test_dragonfly_still_disallows_size(self):
        self.assertFalse(self.validator.is_valid({"dbServers": [{
            "name": "cache", "type": "dragonfly", "plan": "nano", "size": "1Gi",
        }]}))

    def test_other_workloads_keep_pico(self):
        for engine, version in (("cnpg", "16"), ("pxc", "8.0"), ("ferretdb", "16")):
            with self.subTest(engine=engine):
                self.validator.validate({"dbServers": [{
                    "name": "db", "type": engine, "plan": "pico", "version": version, "size": "1Gi",
                }]})
        self.validator.validate({"services": [{"name": "web", "image": "nginx", "plan": "pico"}]})

    def test_psmdb_still_requires_micro(self):
        db = {"name": "db", "type": "psmdb", "plan": "nano", "version": "8.0", "size": "1Gi"}
        self.assertFalse(self.validator.is_valid({"dbServers": [db]}))
        db["plan"] = "micro"
        self.validator.validate({"dbServers": [db]})


if __name__ == "__main__":
    unittest.main()
