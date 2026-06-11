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

        if data.get("redirect_uri") is not None:
            auth.redirect_uri = data["redirect_uri"]

        if data.get("scope") is not None and auth.scope is None:
            auth.scope = data["scope"]

        return auth

    def save_auth(self, auth):
        data = {
            "access_token": auth.access_token,
            "expires_at": auth.expires_at,
            "refresh_token": auth.refresh_token,
        }

        redirect_uri = getattr(auth, "redirect_uri", None)
        if redirect_uri is not None:
            data["redirect_uri"] = redirect_uri

        scope = getattr(auth, "scope", None)
        if scope is not None:
            if isinstance(scope, str):
                data["scope"] = scope
            else:
                data["scope"] = " ".join(scope)

        return self.save(data)
