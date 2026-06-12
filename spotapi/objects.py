from .object_specs import SPOTIFY_OBJECT_SPECS


_MISSING = object()
_current_client = None
_CLASS_REGISTRY = {}
_PAGE_FIELDS = ("href", "limit", "next", "offset", "previous", "total")


def set_client(client):
    global _current_client
    _current_client = client


def get_client():
    return _current_client


class SpotifyObject:
    _fetch_method = None

    def __init__(self, data=None, **kwargs):
        if data is None:
            data = kwargs
        elif kwargs:
            data.update(kwargs)

        self._data = data or {}
        self._fetched = False

    def _peek(self, field):
        value = self._data.get(field, _MISSING)
        if value is _MISSING:
            return None
        return value

    def _can_hydrate(self):
        return self.__class__._fetch_method is not None

    def _get(self, field):
        value = self._data.get(field, _MISSING)

        if value is _MISSING and not self._fetched:
            self._fetch()
            value = self._data.get(field, _MISSING)

        if value is _MISSING:
            return None

        return value

    def _get_embedded_field(self, field, key):
        data = self._get(field)

        if (
            not self._fetched
            and self._can_hydrate()
            and (data is None or key not in data)
        ):
            self._fetch()
            data = self._peek(field)

        return data

    def raw(self):
        return self._data

    def _fetch(self):
        if self._fetched or not self._can_hydrate():
            return self

        client = get_client()
        if client is None:
            return self

        object_id = self._peek("id")
        if object_id is None:
            return self

        fresh = self._fetch_object(client, object_id)
        if fresh is not None:
            self._data.update(fresh.raw())
            self._fetched = True

        return self

    def _fetch_object(self, client, object_id):
        return None

    def _object(self, cls, field):
        data = self._get(field)
        if data is None:
            return None
        return cls(data)

    def _objects(self, cls, field):
        data = self._get(field)
        if data is None:
            return ()
        return [cls(item) for item in data]

    def _typed_object(self, field, type_map):
        data = self._get(field)
        if data is None:
            return None
        return _resolve_typed_item(data, type_map)

    def _typed_objects(self, field, type_map):
        data = self._get(field)
        if data is None:
            return ()
        return [_resolve_typed_item(item, type_map) for item in data]

    def __repr__(self):
        cls = self.__class__.__name__
        name = self._peek("name")
        object_id = self._peek("id")

        if name is not None and object_id is not None:
            return "<{} name={!r} id={!r}>".format(cls, name, object_id)
        if object_id is not None:
            return "<{} id={!r}>".format(cls, object_id)
        return "<{}>".format(cls)

    def __str__(self):
        try:
            import json
        except ImportError:
            return repr(self._data)

        try:
            return json.dumps(self._data, indent=2, sort_keys=True)
        except TypeError:
            return repr(self._data)


class Page(SpotifyObject):
    _item_class = None

    @property
    def items(self):
        data = self._peek("items")
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

    def __getitem__(self, index):
        return self.items[index]


def _resolve_class(name):
    if name is None:
        return None
    return _CLASS_REGISTRY[name]


def _resolve_typed_item(item, type_map):
    cls_name = type_map.get(item.get("type"))
    if cls_name is None:
        return SpotifyObject(item)
    return _resolve_class(cls_name)(item)


def _field_property(field, empty=None):
    def getter(self):
        value = self._get(field)
        if value is None and empty is not None:
            return empty
        return value

    return property(getter)


def _object_property(cls_name, field):
    def getter(self):
        return self._object(_resolve_class(cls_name), field)

    return property(getter)


def _objects_property(cls_name, field):
    def getter(self):
        return self._objects(_resolve_class(cls_name), field)

    return property(getter)


def _object_by_key_property(field, key, present_cls_name, absent_cls_name, page_method=None):
    def getter(self):
        data = self._get_embedded_field(field, key)

        if data is not None and key in data:
            return _resolve_class(present_cls_name)(data)

        if page_method is not None:
            client = get_client()
            object_id = self._peek("id")
            if client is not None and object_id is not None:
                return getattr(client, page_method)(object_id)

        if data is None:
            return None

        return _resolve_class(absent_cls_name)(data)

    return property(getter)


def _typed_object_property(field, type_map):
    def getter(self):
        return self._typed_object(field, type_map)

    return property(getter)


def _typed_objects_property(field, type_map):
    def getter(self):
        return self._typed_objects(field, type_map)

    return property(getter)


def _property_for_spec(prop):
    field = prop["field"]
    kind = prop.get("kind", "field")

    if kind == "field":
        return _field_property(field)
    if kind == "tuple":
        return _field_property(field, empty=())
    if kind == "object":
        return _object_property(prop["class"], field)
    if kind == "objects":
        return _objects_property(prop["class"], field)
    if kind == "object_by_key":
        return _object_by_key_property(
            field,
            prop["key"],
            prop["present_class"],
            prop["absent_class"],
            prop.get("page_method"),
        )
    if kind == "typed_object":
        return _typed_object_property(field, prop["type_map"])
    if kind == "typed_objects":
        return _typed_objects_property(field, prop["type_map"])

    raise ValueError("unknown property kind: {!r}".format(kind))


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
        attrs[prop["field"]] = _property_for_spec(prop)

    fetch_method = spec.get("fetch_method")
    if fetch_method is not None:
        attrs["_fetch_method"] = fetch_method

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


for _page_field in _PAGE_FIELDS:
    setattr(Page, _page_field, _field_property(_page_field))


make_spotify_classes(SPOTIFY_OBJECT_SPECS)
