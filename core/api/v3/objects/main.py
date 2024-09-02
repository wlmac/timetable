from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from django.conf import settings
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.db.models import Model, QuerySet
from django.http import JsonResponse, QueryDict
from django.urls import NoReverseMatch, reverse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from core.api.utils.last_modified import (
    GenericAPIViewWithDebugInfo,
    GenericAPIViewWithLastModified,
)
from core.api.utils.mixins import LookupField

__all__ = ["ObjectList", "ObjectSingle", "ObjectRetrieve", "ObjectNew"]

from core.api.utils.polymorphism import ObjectAPIView, get_providers_by_operation


@extend_schema(
    tags=["Objects"],
    operation_id="api3_obj_list",
    parameters=[
        OpenApiParameter(
            name="type",
            location="path",
            type=str,
            enum=get_providers_by_operation("list"),
            description="Which object provider to use",
        ),
        # OpenApiParameter(
        #     name="lookup", location="query", type=int, description="Lookup field", required=False, default="id"),
    ],
)
class ObjectList(
    GenericAPIViewWithLastModified,
    GenericAPIViewWithDebugInfo,
    ObjectAPIView,
    generics.ListAPIView,
):
    """
    Endpoint for listing objects with various filters.
    """

    mutate = False
    detail = False
    kind = "list"
    FALSE_VALUES = ["false", "0"]
    TRUE_VALUES = ["true", "1"]

    def get_last_modified(self):
        try:
            return self.provider.get_last_modified_queryset()
        except ObjectDoesNotExist:
            return None

    def get_admin_url(self):
        model: Model = self.provider.model
        try:
            return reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            )
        except NoReverseMatch:
            return None

    def __convert_query_params__(self, query_params: QueryDict) -> List[Tuple]:
        """
        Removes non-filter params from query_params and converts them to the correct type.
        :param query_params: QueryDict
        :return: Tuple[List[Tuple], str] (params)
        """
        k_filters = []
        for key, value in query_params.lists():
            if (
                key
                in settings.IGNORED_QUERY_PARAMS + self.provider.listing_filters_ignore
            ):
                continue
            if key not in self.listing_filters:
                raise BadRequest(
                    f"{key} is not a valid filter for {self.provider.model.__name__} listing. Valid filters are: {', '.join(self.listing_filters.keys())}."
                )
            lookup_type = self.listing_filters[key]
            if isinstance(value, list):
                k_filters.append(
                    (
                        key,
                        [self.__convert_type__(item, lookup_type) for item in value],
                    )
                )
            else:
                k_filters.append((key, self.__convert_type__(value, lookup_type)))
        return k_filters

    def __convert_type__(self, lookup_value: str, lookup_type: Callable) -> object:
        lookup_value = lookup_value.casefold()
        if lookup_type is bool:
            if lookup_value in self.FALSE_VALUES:
                return False
            elif lookup_value in self.TRUE_VALUES:
                return True
            else:
                raise BadRequest(
                    f'Invalid value for boolean filter: {lookup_value}. Accepted values for True are {" or ".join(self.TRUE_VALUES)} and for False they are {" or ".join(self.FALSE_VALUES)}'
                )
        if isinstance(lookup_type, list):
            """
            there are multiple types that are accepted for this filter. See which one matches.
            """
            for type_group in lookup_type:
                type_, category = type_group
                if isinstance(lookup_value, type_):
                    try:
                        return {
                            "item": type_(lookup_value),
                            "category": category,
                        }
                    except ValueError:
                        continue
        return lookup_type(lookup_value)

    @staticmethod
    def __compile_filters__(query_params: List) -> Dict:
        filters = {}
        if not query_params:
            # No query params, return None to avoid wastefully filtering.
            return None
        for item in query_params:
            lookup_filter, lookup_value = item

            if isinstance(lookup_value, list) and len(lookup_value) > 1:
                if isinstance(lookup_value[0], dict):
                    filters[f"{lookup_filter}__{lookup_value['category']}__in"] = (
                        # todo add option to use ID or specified field (fix option)
                        lookup_value["item"]
                        if not isinstance(lookup_value["item"], list)
                        else lookup_value["item"][0]
                    )
                else:
                    filters[f"{lookup_filter}__in"] = lookup_value
            else:
                if isinstance(lookup_value, list):
                    lookup_value = lookup_value[0]
                if isinstance(lookup_value, dict):
                    filters[f"{lookup_filter}__{lookup_value['category']}"] = (
                        lookup_value["item"]
                        if not isinstance(lookup_value["item"], list)
                        else lookup_value["item"][0]
                    )
                else:
                    filters[lookup_filter] = lookup_value
        return filters

    def get_queryset(self):
        queryset: QuerySet = self.provider.get_queryset(self.request)
        query_params = self.__convert_query_params__(self.request.query_params)
        filters = self.__compile_filters__(query_params=query_params)
        if filters:
            return queryset.filter(**filters).distinct()
        return queryset

    def get(self, request, *args, **kwargs):
        allow_list = getattr(self.provider, "allow_list", True)
        if not allow_list:
            return JsonResponse({"detail": "listing not allowed"}, status=422)
        response = super().get(self, request, *args, **kwargs)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
            response.data["previous"] = response.data["previous"].replace(
                "http://", "https://"
            )
        return response


@extend_schema(
    tags=["Objects"],
    operation_id="api3_obj_new",
    parameters=[
        OpenApiParameter(
            name="type",
            location="path",
            type=str,
            enum=get_providers_by_operation("new"),
            description="Which object provider to use",
        ),
    ],
)
class ObjectNew(ObjectAPIView, LookupField, generics.CreateAPIView):
    """
    Endpoint for creating new objects.
    """

    mutate = True
    detail = None
    kind = "new"

    def get_queryset(self):
        return self.provider.get_queryset(self.request)

    def post(self, *args, **kwargs):
        if not self.provider.allow_new:
            return JsonResponse({"detail": "creating not allowed"}, status=422)
        return super().post(*args, **kwargs)


@extend_schema(
    tags=["Objects"],
    operation_id="api3_obj_retrieve",
    parameters=[
        OpenApiParameter(
            name="type",
            location="path",
            type=str,
            enum=get_providers_by_operation("retrieve"),
            description="Which object provider to use",
        ),
    ],
)
class ObjectRetrieve(
    ObjectAPIView,
    LookupField,
    generics.RetrieveAPIView,
    GenericAPIViewWithDebugInfo,
    GenericAPIViewWithLastModified,
):
    """
    Endpoint for retrieving objects with various lookups.
    """

    mutate = False
    detail = True
    kind = "retrieve"

    def get_admin_url(self):
        model: Model = self.provider.model
        try:
            return reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            )
        except NoReverseMatch:
            return None

    def get_last_modified(self):
        try:
            return self.provider.get_last_modified(self)
        except ObjectDoesNotExist:
            return None

    def get_queryset(self):
        return self.provider.get_queryset(self.request)


@extend_schema(
    tags=["Objects"],
    operation_id="api3_obj_single",
    parameters=[
        OpenApiParameter(
            name="type",
            location="path",
            type=str,
            enum=get_providers_by_operation("single"),
            description="Which object provider to use",
        ),
    ],
)
class ObjectSingle(
    ObjectAPIView, LookupField, generics.DestroyAPIView, generics.UpdateAPIView
):
    """
    Endpoint for editing objects with support for lookups.
    """

    mutate = True
    detail = None
    kind = "single"

    def check_allow_single(self) -> JsonResponse | None:
        allow_single = getattr(self.provider, "allow_single", True)
        if not allow_single:
            return JsonResponse({"detail": "editing/deletion not allowed"}, status=422)
        return None

    def delete(self, *args, **kwargs):
        if x := self.check_allow_single():
            return x
        if getattr(self.provider, "delete", None):
            return self.provider.delete(self, *args, **kwargs)
        return super().delete(*args, **kwargs)

    def put(self, *args, **kwargs):
        if x := self.check_allow_single():
            return x
        return super().put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        if x := self.check_allow_single():
            return x
        return super().patch(*args, **kwargs)

    def get_admin_url(self):
        model: Model = self.provider.model
        try:
            return reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            )
        except NoReverseMatch:
            return None

    def get_queryset(self):
        return self.provider.get_queryset(self.request)
