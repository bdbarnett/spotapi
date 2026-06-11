from .object_specs import SPOTIFY_OBJECT_SPECS


_MISSING = object()
_current_client = None
_CLASS_REGISTRY = {}


def set_client(client):
    global _current_client
    _current_client = client


def get_client():
    return _current_client


class SpotifyObject:
    def __init__(self, data=None, **kwargs):
        if data is None:
            data = kwargs
        elif kwargs:
            data.update(kwargs)

        self._data = data or {}
        self._fetched = False

    def _get(self, field, fetch=True):
        value = self._data.get(field, _MISSING)

        if value is _MISSING and fetch and not self._fetched:
            self._fetch()
            value = self._data.get(field, _MISSING)

        if value is _MISSING:
            return None

        return value

    def raw(self):
        return self._data

    def _fetch(self):
        if self._fetched:
            return self

        self._fetched = True

        client = get_client()
        if client is None:
            return self

        object_id = self._get("id", fetch=False)
        if object_id is None:
            return self

        fresh = self._fetch_object(client, object_id)
        if fresh is not None:
            self._data.update(fresh.raw())

        return self

    def _fetch_object(self, client, object_id):
        return None

    def _object(self, cls, field, fetch=True):
        data = self._get(field, fetch=fetch)
        if data is None:
            return None
        return cls(data)

    def _objects(self, cls, field, fetch=True):
        data = self._get(field, fetch=fetch)
        if data is None:
            return ()
        return [cls(item) for item in data]

    def _typed_object(self, field, type_map, fetch=True):
        data = self._get(field, fetch=fetch)
        if data is None:
            return None

        cls_name = type_map.get(data.get("type"))
        if cls_name is None:
            return SpotifyObject(data)

        return _resolve_class(cls_name)(data)

    def _typed_objects(self, field, type_map, fetch=True):
        data = self._get(field, fetch=fetch)
        if data is None:
            return ()

        items = []
        for item in data:
            cls_name = type_map.get(item.get("type"))
            if cls_name is None:
                items.append(SpotifyObject(item))
            else:
                items.append(_resolve_class(cls_name)(item))
        return items

    def __repr__(self):
        cls = self.__class__.__name__
        name = self._get("name", fetch=False)
        object_id = self._get("id", fetch=False)

        if name is not None and object_id is not None:
            return "<{} name={!r} id={!r}>".format(cls, name, object_id)
        if object_id is not None:
            return "<{} id={!r}>".format(cls, object_id)
        return "<{}>".format(cls)


class Page(SpotifyObject):
    _item_class = None

    @property
    def href(self):
        return self._get("href", fetch=False)

    @property
    def limit(self):
        return self._get("limit", fetch=False)

    @property
    def next(self):
        return self._get("next", fetch=False)

    @property
    def offset(self):
        return self._get("offset", fetch=False)

    @property
    def previous(self):
        return self._get("previous", fetch=False)

    @property
    def total(self):
        return self._get("total", fetch=False)

    @property
    def items(self):
        data = self._get("items", fetch=False)
        if data is None:
            return ()

        cls = _resolve_class(self._item_class)
        if cls is None:
            return data

        return [cls(item) for item in data]

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


def _resolve_class(name):
    if name is None:
        return None
    return _CLASS_REGISTRY[name]


def _field_property(field, fetch):
    def getter(self):
        return self._get(field, fetch=fetch)

    return property(getter)


def _object_property(cls_name, field, fetch):
    def getter(self):
        return self._object(_resolve_class(cls_name), field, fetch=fetch)

    return property(getter)


def _objects_property(cls_name, field, fetch):
    def getter(self):
        return self._objects(_resolve_class(cls_name), field, fetch=fetch)

    return property(getter)


def _object_by_key_property(field, key, present_cls_name, absent_cls_name, fetch):
    def getter(self):
        data = self._get(field, fetch=fetch)
        if data is None:
            return None

        if key not in data and fetch and not self._fetched:
            self._fetch()
            data = self._get(field, fetch=False)
            if data is None:
                return None

        if key in data:
            cls = _resolve_class(present_cls_name)
        else:
            cls = _resolve_class(absent_cls_name)

        return cls(data)

    return property(getter)


def _typed_object_property(field, type_map, fetch):
    def getter(self):
        return self._typed_object(field, type_map, fetch=fetch)

    return property(getter)


def _typed_objects_property(field, type_map, fetch):
    def getter(self):
        return self._typed_objects(field, type_map, fetch=fetch)

    return property(getter)


def _tuple_field_property(field, fetch):
    def getter(self):
        value = self._get(field, fetch=fetch)
        if value is None:
            return ()
        return value

    return property(getter)


def make_spotify_class(spec):
    name = spec["name"]
    attrs = {}

    base = spec.get("base")
    if base is not None:
        base_class = _resolve_class(base)
        attrs["_item_class"] = spec.get("item_class")
    else:
        base_class = SpotifyObject

    for prop in spec.get("properties", ()):
        field = prop["field"]
        fetch = prop.get("fetch", False)
        kind = prop.get("kind", "field")

        if kind == "field":
            attrs[field] = _field_property(field, fetch)
        elif kind == "tuple":
            attrs[field] = _tuple_field_property(field, fetch)
        elif kind == "object":
            attrs[field] = _object_property(prop["class"], field, fetch)
        elif kind == "objects":
            attrs[field] = _objects_property(prop["class"], field, fetch)
        elif kind == "object_by_key":
            attrs[field] = _object_by_key_property(
                field,
                prop["key"],
                prop["present_class"],
                prop["absent_class"],
                fetch,
            )
        elif kind == "typed_object":
            attrs[field] = _typed_object_property(field, prop["type_map"], fetch)
        elif kind == "typed_objects":
            attrs[field] = _typed_objects_property(field, prop["type_map"], fetch)

    fetch_method = spec.get("fetch_method")
    if fetch_method is not None:
        def _fetch_object(self, client, object_id):
            return getattr(client, fetch_method)(object_id)

        attrs["_fetch_object"] = _fetch_object

    return type(name, (base_class,), attrs)


def make_spotify_classes(specs):
    classes = {}
    _CLASS_REGISTRY["Page"] = Page
    globals()["Page"] = Page

    for spec in specs:
        cls = make_spotify_class(spec)
        classes[spec["name"]] = cls
        _CLASS_REGISTRY[spec["name"]] = cls
        globals()[spec["name"]] = cls
    return classes


make_spotify_classes(SPOTIFY_OBJECT_SPECS)
