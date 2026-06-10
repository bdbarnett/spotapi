import unittest

from spotapi import EXAMPLE_SCOPES


class ScopeTest(unittest.TestCase):
    def test_example_scopes_include_read_and_write_permissions(self):
        scopes = set(EXAMPLE_SCOPES)

        self.assertIn("user-read-email", scopes)
        self.assertIn("user-library-read", scopes)
        self.assertIn("user-library-modify", scopes)
        self.assertIn("playlist-read-private", scopes)
        self.assertIn("playlist-modify-private", scopes)
        self.assertIn("playlist-modify-public", scopes)
        self.assertIn("ugc-image-upload", scopes)
        self.assertIn("user-modify-playback-state", scopes)


if __name__ == "__main__":
    unittest.main()
