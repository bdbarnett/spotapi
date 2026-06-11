from _bootstrap import bootstrap

bootstrap()

from spotapi import SpotifyClient, credentials_from_config, load_config


class RequestsTransport:
    def __init__(self, requests_module):
        self.requests = requests_module

    def get(self, url, headers=None):
        return self.requests.get(url, headers=headers)

    def post(self, url, data=None, headers=None):
        return self.requests.post(url, data=data, headers=headers)


def main():
    try:
        import requests
    except ImportError:
        raise SystemExit("Install requests or pass a transport for your runtime")

    config = load_config()
    client_id, client_secret = credentials_from_config(config)
    transport = RequestsTransport(requests)
    client = SpotifyClient(client_id=client_id, client_secret=client_secret, transport=transport)
    markets = client.available_markets()

    print("markets:", len(markets))
    print(", ".join(markets[:10]))


if __name__ == "__main__":
    main()
