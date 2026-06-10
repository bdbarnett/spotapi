import unittest

from scripts.endpoint_coverage import endpoint_coverage, openapi_endpoints


class EndpointCoverageTest(unittest.TestCase):
    def test_openapi_endpoints_extracts_supported_methods(self):
        schema = {
            "paths": {
                "/tracks/{id}": {
                    "get": {"operationId": "get-track"},
                    "parameters": [],
                },
                "/me/tracks": {
                    "get": {"operationId": "get-users-saved-tracks"},
                    "put": {"operationId": "save-tracks-user"},
                    "delete": {"operationId": "remove-tracks-user"},
                },
            },
        }

        self.assertEqual(
            openapi_endpoints(schema),
            (
                ("DELETE", "/me/tracks", "remove-tracks-user"),
                ("GET", "/me/tracks", "get-users-saved-tracks"),
                ("PUT", "/me/tracks", "save-tracks-user"),
                ("GET", "/tracks/{id}", "get-track"),
            ),
        )

    def test_endpoint_coverage_reports_missing_and_extra_endpoints(self):
        schema = {
            "paths": {
                "/tracks/{id}": {
                    "get": {"operationId": "get-track"},
                },
                "/artists/{id}/related-artists": {
                    "get": {"operationId": "get-an-artists-related-artists"},
                },
            },
        }

        report = endpoint_coverage(
            schema,
            implemented=(
                ("GET", "/tracks/{id}"),
                ("GET", "/not-in-schema"),
            ),
        )

        self.assertEqual(report["covered"], (("GET", "/tracks/{id}", "get-track"),))
        self.assertEqual(
            report["missing"],
            (("GET", "/artists/{id}/related-artists", "get-an-artists-related-artists"),),
        )
        self.assertEqual(report["extra"], (("GET", "/not-in-schema"),))


if __name__ == "__main__":
    unittest.main()
