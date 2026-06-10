import unittest

from spotapi.schema_coverage import OPENAPI_SCHEMA_NAMES, SCHEMA_TO_SPEC, SKIPPED_SCHEMA_NAMES, uncovered_schema_names


class SchemaCoverageTest(unittest.TestCase):
    def test_all_non_primitive_openapi_schemas_are_covered(self):
        self.assertEqual(uncovered_schema_names(), ())

    def test_skipped_schemas_are_primitive_aliases(self):
        self.assertEqual(
            set(SKIPPED_SCHEMA_NAMES),
            {"Key", "Loudness", "Mode", "Tempo", "TimeSignature"},
        )

    def test_non_primitive_schemas_have_explicit_mappings(self):
        missing = set(OPENAPI_SCHEMA_NAMES) - set(SKIPPED_SCHEMA_NAMES) - set(SCHEMA_TO_SPEC)

        self.assertEqual(missing, set())


if __name__ == "__main__":
    unittest.main()
