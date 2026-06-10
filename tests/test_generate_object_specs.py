import unittest

from scripts.generate_object_specs import build_specs, schema_to_class_name


class GenerateObjectSpecsTest(unittest.TestCase):
    def test_schema_to_class_name_strips_common_suffixes(self):
        self.assertEqual(schema_to_class_name("TrackObject"), "Track")
        self.assertEqual(schema_to_class_name("EpisodeBase"), "Episode")

    def test_schema_to_class_name_uses_curated_overrides(self):
        self.assertEqual(schema_to_class_name("SimplifiedTrackObject"), "Track")
        self.assertEqual(schema_to_class_name("TrackRestrictionObject"), "Restriction")
        self.assertEqual(schema_to_class_name("PagingSimplifiedTrackObject"), "TrackPage")
        self.assertEqual(schema_to_class_name("PagingFeaturedPlaylistObject"), "FeaturedPlaylists")
        self.assertEqual(schema_to_class_name("PublicUserObject"), "User")

    def test_build_specs_maps_refs_and_arrays(self):
        schema = {
            "components": {
                "schemas": {
                    "ArtistObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "images": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/ImageObject"},
                            },
                        },
                    },
                    "ImageObject": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                        },
                    },
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "album": {
                                "allOf": [
                                    {"$ref": "#/components/schemas/AlbumObject"},
                                ],
                            },
                            "available_markets": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "restrictions": {
                                "type": "object",
                                "allOf": [
                                    {"$ref": "#/components/schemas/TrackRestrictionObject"},
                                ],
                            },
                        },
                    },
                    "AlbumObject": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["Artist"]["properties"],
            (
                {"field": "id"},
                {"field": "images", "kind": "objects", "class": "Image"},
            ),
        )
        self.assertEqual(
            by_name["Track"]["properties"],
            (
                {"field": "album", "kind": "object", "class": "Album"},
                {"field": "available_markets", "kind": "tuple"},
                {"field": "restrictions", "kind": "object", "class": "Restriction"},
            ),
        )

    def test_build_specs_maps_array_items_wrapped_in_all_of(self):
        schema = {
            "components": {
                "schemas": {
                    "TrackListObject": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/TrackObject"},
                                    ],
                                },
                            },
                        },
                    },
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["TrackList"]["properties"],
            (
                {"field": "items", "kind": "objects", "class": "Track"},
            ),
        )

    def test_build_specs_converts_paging_objects_to_page_specs(self):
        schema = {
            "components": {
                "schemas": {
                    "PagingObject": {
                        "type": "object",
                        "properties": {
                            "href": {"type": "string"},
                            "limit": {"type": "integer"},
                            "next": {"type": "string"},
                            "offset": {"type": "integer"},
                            "previous": {"type": "string"},
                            "total": {"type": "integer"},
                        },
                    },
                    "PagingTrackObject": {
                        "type": "object",
                        "properties": {
                            "href": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/TrackObject"},
                            },
                            "limit": {"type": "integer"},
                            "next": {"type": "string"},
                            "offset": {"type": "integer"},
                            "previous": {"type": "string"},
                            "total": {"type": "integer"},
                        },
                    },
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(by_name["Paging"], {"name": "Paging", "base": "Page"})
        self.assertEqual(by_name["TrackPage"], {"name": "TrackPage", "base": "Paging", "item_class": "Track"})

    def test_build_specs_preserves_extra_page_properties(self):
        schema = {
            "components": {
                "schemas": {
                    "CursorPagingPlayHistoryObject": {
                        "type": "object",
                        "properties": {
                            "cursors": {"$ref": "#/components/schemas/CursorObject"},
                            "href": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/PlayHistoryObject"},
                            },
                            "limit": {"type": "integer"},
                            "next": {"type": "string"},
                            "total": {"type": "integer"},
                        },
                    },
                    "CursorObject": {
                        "type": "object",
                        "properties": {
                            "after": {"type": "string"},
                        },
                    },
                    "PlayHistoryObject": {
                        "type": "object",
                        "properties": {
                            "played_at": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["PlayHistoryCursorPage"],
            {
                "name": "PlayHistoryCursorPage",
                "base": "Paging",
                "item_class": "PlayHistory",
                "properties": (
                    {"field": "cursors", "kind": "object", "class": "Cursor"},
                ),
            },
        )

    def test_build_specs_maps_one_of_refs_to_typed_object(self):
        schema = {
            "components": {
                "schemas": {
                    "CurrentlyPlayingContextObject": {
                        "type": "object",
                        "properties": {
                            "item": {
                                "oneOf": [
                                    {"$ref": "#/components/schemas/TrackObject"},
                                    {"$ref": "#/components/schemas/EpisodeObject"},
                                ],
                                "discriminator": {"propertyName": "type"},
                            },
                        },
                    },
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "EpisodeObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["CurrentlyPlaying"]["properties"],
            (
                {
                    "field": "item",
                    "kind": "typed_object",
                    "type_map": {
                        "episode": "Episode",
                        "track": "Track",
                    },
                },
            ),
        )

    def test_build_specs_maps_array_one_of_refs_to_typed_objects(self):
        schema = {
            "components": {
                "schemas": {
                    "QueueObject": {
                        "type": "object",
                        "properties": {
                            "queue": {
                                "type": "array",
                                "items": {
                                    "oneOf": [
                                        {"$ref": "#/components/schemas/TrackObject"},
                                        {"$ref": "#/components/schemas/EpisodeObject"},
                                    ],
                                    "discriminator": {"propertyName": "type"},
                                },
                            },
                        },
                    },
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "EpisodeObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["Queue"]["properties"],
            (
                {
                    "field": "queue",
                    "kind": "typed_objects",
                    "type_map": {
                        "episode": "Episode",
                        "track": "Track",
                    },
                },
            ),
        )

    def test_build_specs_merges_schemas_with_same_class_name(self):
        schema = {
            "components": {
                "schemas": {
                    "AlbumBase": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "AlbumObject": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0]["name"], "Album")
        self.assertEqual(
            specs[0]["properties"],
            (
                {"field": "id"},
                {"field": "name"},
            ),
        )

    def test_build_specs_merges_curated_override_names(self):
        schema = {
            "components": {
                "schemas": {
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "SimplifiedTrackObject": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                        },
                    },
                    "TrackRestrictionObject": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string"},
                        },
                    },
                    "AlbumRestrictionObject": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(sorted(by_name), ["Restriction", "Track"])
        self.assertEqual(
            by_name["Track"]["properties"],
            (
                {"field": "id"},
                {"field": "name"},
            ),
        )
        self.assertEqual(by_name["Restriction"]["properties"], ({"field": "reason"},))

    def test_build_specs_adds_fetch_methods_for_fetchable_objects(self):
        schema = {
            "components": {
                "schemas": {
                    "TrackObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "ImageObject": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(by_name["Track"]["fetch_method"], "track")
        self.assertNotIn("fetch_method", by_name["Image"])

    def test_build_specs_generates_selected_response_wrappers(self):
        schema = {
            "components": {
                "schemas": {
                    "AlbumObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "ArtistObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "PagingSimplifiedAlbumObject": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/AlbumObject"},
                            },
                        },
                    },
                    "PagingArtistObject": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/ArtistObject"},
                            },
                        },
                    },
                },
                "responses": {
                    "PlaylistSnapshotId": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "snapshot_id": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                    "SearchItems": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "albums": {
                                            "$ref": "#/components/schemas/PagingSimplifiedAlbumObject",
                                        },
                                        "artists": {
                                            "$ref": "#/components/schemas/PagingArtistObject",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(by_name["SnapshotResult"]["properties"], ({"field": "snapshot_id"},))
        self.assertEqual(
            by_name["SearchResults"]["properties"],
            (
                {"field": "albums", "kind": "object", "class": "AlbumPage"},
                {"field": "artists", "kind": "object", "class": "ArtistPage"},
            ),
        )

    def test_build_specs_unwraps_selected_nested_response_wrappers(self):
        schema = {
            "components": {
                "schemas": {
                    "CategoryObject": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                    "PagingObject": {
                        "type": "object",
                        "properties": {
                            "href": {"type": "string"},
                            "limit": {"type": "integer"},
                        },
                    },
                },
                "responses": {
                    "PagedCategories": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "categories": {
                                            "type": "object",
                                            "allOf": [
                                                {"$ref": "#/components/schemas/PagingObject"},
                                                {
                                                    "type": "object",
                                                    "properties": {
                                                        "items": {
                                                            "type": "array",
                                                            "items": {
                                                                "$ref": "#/components/schemas/CategoryObject",
                                                            },
                                                        },
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

        specs = build_specs(schema)
        by_name = dict((spec["name"], spec) for spec in specs)

        self.assertEqual(
            by_name["CategoryPage"]["properties"],
            (
                {"field": "href"},
                {"field": "items", "kind": "objects", "class": "Category"},
                {"field": "limit"},
            ),
        )


if __name__ == "__main__":
    unittest.main()
