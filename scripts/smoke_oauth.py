import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from spotapi import user_client


def main():
    try:
        client = user_client()
    except Exception as error:
        raise SystemExit(str(error))

    user = client.me()

    print("id:", user.id)
    print("display_name:", user.display_name)
    print("product:", user.product)


if __name__ == "__main__":
    main()
