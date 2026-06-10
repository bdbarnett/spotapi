class TokenCache:
    def __init__(self, path="tokens.json"):
        self.path = path

    def load(self):
        try:
            import json
        except ImportError:
            return {}

        try:
            with open(self.path) as file:
                return json.load(file)
        except OSError:
            return {}

    def save(self, data):
        try:
            import json
        except ImportError:
            return False

        with open(self.path, "w") as file:
            json.dump(data, file)

        return True

    def load_auth(self, auth):
        data = self.load()
        auth.access_token = data.get("access_token")
        auth.expires_at = data.get("expires_at", 0)

        if data.get("refresh_token") is not None:
            auth.refresh_token = data["refresh_token"]

        return auth

    def save_auth(self, auth):
        return self.save(
            {
                "access_token": auth.access_token,
                "expires_at": auth.expires_at,
                "refresh_token": auth.refresh_token,
            }
        )
