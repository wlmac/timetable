import dataclasses
from functools import wraps
from typing import Any, Callable, Dict, Final, List, Optional, Sequence, Tuple, Type

from drf_spectacular.drainage import set_override
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import F, OpenApiExample
from memoization import cached
from rest_framework.serializers import Serializer

from core.api.utils.polymorphism import (
    get_path_by_provider,
    get_provider,
    get_providers_by_operation,
    providers,
)
from core.api.v3.objects.base import BaseProvider
from core.utils.types import (
    ObjectModificationData,
    ProviderDetails,
    SingleOperationData,
)


def metro_extend_schema_serializer(  # modified version of drf_spectacular.utils.extend_schema_serializer
    klass: Type[Serializer],
    many: Optional[bool] = None,
    exclude_fields: Optional[Sequence[str]] = None,
    deprecate_fields: Optional[Sequence[str]] = None,
    examples: Optional[Sequence[OpenApiExample]] = None,
    extensions: Optional[Dict[str, Any]] = None,
    component_name: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Function for modifying the behavior of a serializer class. Intended for overriding default serializer
    behavior that can't be influenced through: func:`~drf_spectacular.utils.extend_schema`.

    :param klass: The serializer class to modify.
    :param many: Override how the serializer is initialized. Mainly used to coerce the list view detection
        heuristic to acknowledge a non-list serializer.
    :param exclude_fields: Fields to ignore while processing the serializer. Only affects the
        schema. Fields will still be exposed through the API.
    :param deprecate_fields: Fields to mark as deprecated while processing the serializer.
    :param examples: Define example data for the serializer.
    :param extensions: Specification extensions, e.g., ``x-is-dynamic``, etc.
    :param component_name: Override the default class name extraction.
    """
    if many is not None:
        set_override(klass, "many", many)
    if exclude_fields:
        set_override(klass, "exclude_fields", exclude_fields)
    if deprecate_fields:
        set_override(klass, "deprecate_fields", deprecate_fields)
    if examples:
        set_override(klass, "examples", examples)
    if extensions:
        set_override(klass, "extensions", extensions)
    if component_name:
        set_override(klass, "component_name", component_name)

    return klass


def dynamic_envelope(serializer_class: Type[Serializer], many=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            component_name = (
                f'Enveloped{serializer_class.__name__.replace("Serializer", "")}'
            )
            component_name += "List" if many else ""

            metro_extend_schema_serializer(
                serializer_class, many=False, component_name=component_name
            )

            response = view_func(*args, **kwargs)

            return response

        return wrapped_view

    return decorator


@cached
def run_fixers(result, generator, request, public):
    """
    Run fixers on the schema to ensure that the API docs are properly formatted.

    Note: this should ALWAYS return the same result for the same input as it's cached to improve performance.
    """
    fixers = [Api3ObjSpliter]
    if fixers is None:
        raise ValueError("No fixers found, API3 obj docs will be broken.")
    for fixer_obj in fixers:
        fixer = fixer_obj(result)
        fixer.run()
        result = fixer.schema
    return result


class Api3ObjSpliter:
    """
    Split the API3 schema into the different paths based on the object type and provider
    """

    defaults = {
        "tags": ["Objects", "V3"],
    }

    def __init__(self, schema):
        self.operation_data = ObjectModificationData()
        self.keys_to_delete: Tuple = ()
        self.schema = schema
        self._provider_details: Dict[str, ProviderDetails] = {}

    def run(self):
        # ObjectModificationData._make
        paths = self.schema["paths"]
        self.set_obj_paths(paths)

        for _, provider in providers.items():
            ...
            # print(self._get_data_from_provider(provider))
        for operation in dataclasses.fields(self.operation_data):
            self.create_obj_views(operation)

        self.del_obj_paths()

    def del_obj_paths(self) -> None:
        for path in self.keys_to_delete:
            del self.schema["paths"][path]

    def set_obj_paths(self, paths: Dict[str, dict]) -> List[Tuple[str, dict]]:
        PATH_PREFIX = "/api/v3/obj/{type}"
        _obj_paths = [
            (path, value)
            for path, value in paths.items()
            if path.startswith(PATH_PREFIX)
        ]
        self.keys_to_delete = tuple(
            [path for path, _ in _obj_paths]
        )  # designates the api3 obj polymorphic paths to be deleted.
        for _, value in _obj_paths:
            http_method = list(value.keys())[0]
            operation_id = value[http_method]["operationId"]
            name = self._get_name_from_id(operation_id)
            # set values for ObjectModificationData
            print(f"Setting {name} for {http_method} with OperationID: {operation_id}")
            # self._provider_details[name] = ProviderDetails(

            insertable_value = SingleOperationData(
                operation=name,
                data=value[http_method],
                providers=get_providers_by_operation(name, return_provider=True),
            )
            setattr(self.operation_data, name, insertable_value)
        if not self.operation_data:
            raise ValueError("No paths found, API3 obj docs will be broken.")

    def _generate_data(self):
        for provider_name, provider_obj in providers.items():
            self._provider_details[provider_name] = ProviderDetails(
                provider=provider_obj,
                operations_supported=dict(),
            )

    @staticmethod
    def _get_data_from_provider(provider: BaseProvider) -> tuple:
        """Returns a tuple of operations supported and the serializers for each
        e.g. UserProvider {'single': <class 'core.api.v3.objects.user.UserSerializer'>, 'new': <class 'core.api.v3.objects.user.NewSerializer'>, 'list': <class 'core.api.v3.objects.user.ListSerializer'>, 'retrieve': <class 'core.api.v3.objects.user.UserSerializer'>}
        """
        supported_operations: dict = {
            "single": None,
            "new": None,
            "list": None,
            "retrieve": None,
        }
        data = provider.raw_serializers.items()
        for operation, serializer in data:
            if operation == "_":
                continue
            supported_operations[operation] = serializer

        supported_operations = {
            operation: (
                provider.raw_serializers["_"] if serializer is None else serializer
            )
            for operation, serializer in supported_operations.items()
        }
        return supported_operations.items()

    @staticmethod
    def _get_name_from_id(operation_id: str) -> str:
        return operation_id.split("_")[-1]

    @staticmethod
    def get_providers_from_name(enum: List[str]) -> List[BaseProvider]:
        return [get_provider(key) for key in enum]

    def create_obj_views(self, operation: SingleOperationData): ...


class MetroSchemaGenerator(SchemaGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_paths_and_endpoints(self):
        """
        Generate (path, method, view) given (path, method, callback) for paths.
        """
        obj3 = set()
        view_endpoints = super()._get_paths_and_endpoints()
        for path, subpath, method, view in view_endpoints:
            if path.startswith("/api/v3/obj/") and "{type}" in path:
                name = view.__class__.__name__.lstrip("Object").casefold()
                print(f"Found path: {name}")
                for provider in get_providers_by_operation(name, return_provider=True):
                    provider: BaseProvider
                    data = Api3ObjSpliter._get_data_from_provider(provider)  # noqa
                    print(path.replace("{type}", get_path_by_provider(provider)))
                    obj3.add(
                        ProviderDetails(
                            provider=provider,
                            operations_supported=data,
                            view=view,
                            url=path.replace(
                                "{type}",
                                get_path_by_provider(provider),
                            ),
                        )
                    )

        # print(f"obj3: {obj3}")
        formatted_obj3 = self._generate_endpoints(obj3)

        view_endpoints.extend(formatted_obj3)
        print(f"View Endpoints: {formatted_obj3}")
        return view_endpoints

    def _generate_endpoints(
        self, obj_data: List[ProviderDetails]
    ) -> List[Tuple[str, str, str, Any]]:
        """
        Generate the endpoints for the API3 objects
        Takes in a list of ProviderDetails and returns a list of tuples in the fmt of (path, path_regex, method, view)
        """
        CONVERTER: Final = {
            "list": ["GET"],
            "new": ["POST"],
            "retrieve": ["GET"],
            "single": ["PUT", "PATCH", "DELETE"],
        }
        endpoints = []
        for obj in obj_data:
            for operation, serializer in obj.operations_supported:
                for method in CONVERTER[operation]:
                    print(f"Operation: {operation} Method: {method}")
                    endpoints.append(
                        (
                            obj.url,
                            obj.url,
                            method,
                            obj.view,
                        )
                    )

        return endpoints
