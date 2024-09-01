from abc import ABC
from typing import Dict, Final, List, Tuple

from django.db.models.base import ModelBase
from rest_framework.serializers import BaseSerializer

from core.utils.types import APIObjOperations

type SerializerItems = Dict[str, BaseSerializer]


class BaseProvider(ABC, object):
    allow_list: bool = True  # Is the view able to list the model's objects. (e.g. /user would list all users
    allow_new: bool = True  # Is the provider able to create a new object.
    kind: APIObjOperations  # type of view
    listing_filters_ignore: List[str] = []
    raw_serializers: SerializerItems

    @property
    def serializer_class(self):
        return self.serializers.get(self.request.kind)

    @classmethod
    def _run_typechecking(cls):
        get_attrs: Final[str] = ("queryset",)
        required_attrs: Final[Dict[str, type]] = {
            "model": ModelBase,
            "raw_serializers": dict,
        }
        additional_attrs: Final[Dict[str, type]] = {"additional_lookup_fields": list}

        for key in get_attrs:
            if not (
                hasattr(cls, key) or hasattr(cls, f"get_{key}")
            ):  # todo check if callable
                raise AttributeError(
                    f"{cls} must either define {key} or :meth:get_{key}"
                )

        for key, _ in required_attrs.items():
            if not hasattr(cls, key):
                raise AttributeError(f"{cls} must define attr {key} of type {type}")

        # just type checking, doesnt care if value is there or not.
        for key, value in (additional_attrs | required_attrs).items():
            if hasattr(cls, key) and (item := getattr(cls, key)):
                if not isinstance(item, value):
                    raise TypeError(f"{key} must be of type {value}")

        cls._check_serializers()

    @classmethod
    def _check_serializers(cls):
        for key in cls.raw_serializers:
            if key not in ("list", "new", "single", "retrieve", "_"):
                raise AttributeError(
                    f"key {key} is not a valid key for raw_serializers"
                )

    def __new__(cls, request):
        from core.api.utils.polymorphism import splitter

        cls._run_typechecking()

        instance = super().__new__(cls)
        instance.serializers = splitter(cls.raw_serializers)
        return instance

    def __init__(self, request):
        self.request = request

    @classmethod
    def supported_operations(cls) -> Tuple[str]:
        if not issubclass(cls, BaseProvider):
            raise TypeError("This method can only be ran on subclasses of BaseProvider")
        if "_" in cls.raw_serializers.keys():
            return "list", "new", "single", "retrieve"
        return tuple(cls.raw_serializers.keys())
