API_BASE_URL = "https://api.spotify.com/v1"


class TransportError(Exception):
    def __init__(self, message, status=None, data=None):
        Exception.__init__(self, message)
        self.status = status
        self.data = data


def get_json(path_or_url, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    url = build_url(path_or_url, query=query, base_url=base_url)
    request_headers = {}

    if headers:
        request_headers.update(headers)
    if access_token is not None:
        request_headers["Authorization"] = "Bearer " + access_token

    if transport is not None:
        return transport_get_json(transport, url, request_headers)

    return urllib_get_json(url, request_headers)


def post_form_json(url, data, headers=None, transport=None):
    request_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        request_headers.update(headers)

    body = query_string(data)

    if transport is not None:
        return transport_post_form_json(transport, url, body, request_headers)

    return urllib_post_form_json(url, body, request_headers)


def post_json(path_or_url, data=None, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    return request_json("POST", path_or_url, data, access_token, query, headers, transport, base_url)


def put_json(path_or_url, data=None, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    return request_json("PUT", path_or_url, data, access_token, query, headers, transport, base_url)


def delete_json(path_or_url, data=None, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    return request_json("DELETE", path_or_url, data, access_token, query, headers, transport, base_url)


def put_body(path_or_url, body, content_type, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    return request_body("PUT", path_or_url, body, content_type, access_token, query, headers, transport, base_url)


def request_json(method, path_or_url, data=None, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    url = build_url(path_or_url, query=query, base_url=base_url)
    request_headers = {}

    if headers:
        request_headers.update(headers)
    if access_token is not None:
        request_headers["Authorization"] = "Bearer " + access_token

    body = None
    if data is not None:
        request_headers["Content-Type"] = "application/json"
        body = json_dumps(data)

    if transport is not None:
        return transport_request_json(transport, method, url, body, request_headers)

    return urllib_method_json(method, url, body, request_headers)


def request_body(method, path_or_url, body, content_type, access_token=None, query=None, headers=None, transport=None, base_url=API_BASE_URL):
    url = build_url(path_or_url, query=query, base_url=base_url)
    request_headers = {"Content-Type": content_type}

    if headers:
        request_headers.update(headers)
    if access_token is not None:
        request_headers["Authorization"] = "Bearer " + access_token

    if transport is not None:
        return transport_request_body(transport, method, url, body, request_headers)

    return urllib_method_json(method, url, body, request_headers)


def transport_get_json(transport, url, headers):
    if hasattr(transport, "get_json"):
        return transport.get_json(url, headers)

    if hasattr(transport, "get"):
        response = transport.get(url, headers=headers)
        return response_json(response)

    return transport(url, headers)


def transport_post_form_json(transport, url, body, headers):
    if hasattr(transport, "post_form_json"):
        return transport.post_form_json(url, body, headers)

    if hasattr(transport, "post"):
        response = transport.post(url, data=body, headers=headers)
        return response_json(response)

    return transport(url, headers, body)


def transport_request_json(transport, method, url, body, headers):
    if hasattr(transport, "request_json"):
        return transport.request_json(method, url, body, headers)

    method_name = method.lower()
    if hasattr(transport, method_name):
        request_method = getattr(transport, method_name)
        if body is None:
            response = request_method(url, headers=headers)
        else:
            response = request_method(url, data=body, headers=headers)
        return response_json(response)

    return transport(method, url, headers, body)


def transport_request_body(transport, method, url, body, headers):
    if hasattr(transport, "request_body"):
        return transport.request_body(method, url, body, headers)

    method_name = method.lower()
    if hasattr(transport, method_name):
        response = getattr(transport, method_name)(url, data=body, headers=headers)
        return response_json(response)

    return transport(method, url, headers, body)


def response_json(response):
    try:
        status = response_status(response)
        if status == 204:
            return None

        data = parse_response_json(response, status=status)
    finally:
        close_response(response)

    if status is not None and (status < 200 or status >= 300):
        raise TransportError("HTTP status {}".format(status), status=status, data=data)

    return data


def response_status(response):
    if hasattr(response, "status_code"):
        return response.status_code
    if hasattr(response, "status"):
        return response.status
    if hasattr(response, "getcode"):
        return response.getcode()
    return None


def read_response_text(response):
    if hasattr(response, "text"):
        return response.text

    if hasattr(response, "content"):
        content = response.content
        if not isinstance(content, str):
            content = content.decode("utf-8")
        return content

    if hasattr(response, "read"):
        data = response.read()
        if not isinstance(data, str):
            data = data.decode("utf-8")
        return data

    return ""


def parse_response_json(response, status=None):
    if hasattr(response, "json"):
        try:
            return response.json()
        except ValueError:
            if _successful_status(status):
                return None
            raise

    if hasattr(response, "text") or hasattr(response, "content") or hasattr(response, "read"):
        body = read_response_text(response)
        if not body or not body.strip():
            return None

        try:
            return json_loads(body)
        except ValueError:
            if _successful_status(status):
                return None
            raise

    return response


def _successful_status(status):
    return status is not None and 200 <= status < 300


def close_response(response):
    if hasattr(response, "close"):
        response.close()
    elif hasattr(response, "deinit"):
        response.deinit()


def urllib_get_json(url, headers):
    try:
        from urllib.request import Request
    except ImportError:
        raise TransportError("No default HTTP transport is available on this Python runtime")

    return urllib_request_json(Request(url, headers=headers))


def urllib_post_form_json(url, body, headers):
    try:
        from urllib.request import Request
    except ImportError:
        raise TransportError("No default HTTP transport is available on this Python runtime")

    body = body.encode("utf-8")
    return urllib_request_json(Request(url, data=body, headers=headers))


def urllib_method_json(method, url, body, headers):
    try:
        from urllib.request import Request
    except ImportError:
        raise TransportError("No default HTTP transport is available on this Python runtime")

    if body is not None:
        body = body.encode("utf-8")

    return urllib_request_json(Request(url, data=body, headers=headers, method=method))


def urllib_request_json(request):
    try:
        from urllib.request import urlopen
    except ImportError:
        raise TransportError("No default HTTP transport is available on this Python runtime")

    try:
        response = urlopen(request)
        return response_json(response)
    except Exception as error:
        if hasattr(error, "code") and hasattr(error, "read"):
            raw = error.read()
            if not isinstance(raw, str):
                raw = raw.decode("utf-8")
            data = None
            if raw and raw.strip():
                try:
                    data = json_loads(raw)
                except ValueError:
                    data = raw
            raise TransportError("HTTP status {}".format(error.code), status=error.code, data=data)
        raise


def json_loads(data):
    try:
        import json
    except ImportError:
        raise TransportError("No JSON parser is available on this Python runtime")

    if not isinstance(data, str):
        data = data.decode("utf-8")

    return json.loads(data)


def json_dumps(data):
    try:
        import json
    except ImportError:
        raise TransportError("No JSON serializer is available on this Python runtime")

    return json.dumps(data)


def build_url(path_or_url, query=None, base_url=API_BASE_URL):
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        url = path_or_url
    else:
        url = base_url + path_or_url

    encoded = query_string(query)
    if encoded:
        return url + "?" + encoded
    return url


def query_string(query):
    if not query:
        return ""

    parts = []
    for key in query:
        value = query[key]
        if value is not None:
            parts.append(quote(key) + "=" + quote(value))
    return "&".join(parts)


def quote(value):
    value = str(value)

    try:
        from urllib.parse import quote as urllib_quote
        return urllib_quote(value, safe="")
    except ImportError:
        return simple_quote(value)


def unquote_plus(value):
    value = value.replace("+", " ")

    try:
        from urllib.parse import unquote as urllib_unquote
        return urllib_unquote(value)
    except ImportError:
        return simple_unquote(value)


def simple_quote(value):
    safe = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    encoded = []

    for char in value:
        if char in safe:
            encoded.append(char)
        else:
            for byte in char.encode("utf-8"):
                encoded.append("%{:02X}".format(byte))

    return "".join(encoded)


def simple_unquote(value):
    chunks = []
    index = 0
    length = len(value)

    while index < length:
        char = value[index]
        if char == "%" and index + 2 < length:
            hex_value = value[index + 1:index + 3]
            try:
                chunks.append(int(hex_value, 16))
                index += 3
                continue
            except ValueError:
                pass

        for byte in char.encode("utf-8"):
            chunks.append(byte)
        index += 1

    return bytes(chunks).decode("utf-8")
