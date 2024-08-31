from __future__ import annotations

from json import JSONDecodeError
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Set

from django.conf import settings
from django.core.exceptions import BadRequest
from django.db.models import Model, Q
from django.shortcuts import get_object_or_404
from memoization import cached
from rest_framework import generics
from rest_framework.serializers import BaseSerializer

from core.api.v3.objects import *
from core.api.v3.objects.base import BaseProvider
from core.utils.types import APIObjOperations

type IgnoredKey = str | Iterable[str]
type SerializerItems = Dict[str, BaseSerializer]


class SplitDictResult:
    def __init__(self, new: dict, old: dict, default: IgnoredKey):
        self.new = new
        self.old = old
        self.default = default

    def get(self, item) -> Any:
        return self.new.get(item, self.old.get(self.default))

    def __getitem__(self, key):
        return self.get(key)


def split_dict_wrapper(
    ignore: IgnoredKey,
) -> Callable[[Dict[str, Any]], SplitDictResult]:
    """
    Note: this will fail as the dict must be frozen so LRU cache can hash it
    """

    @cached
    def split_dict(dictionary: SerializerItems) -> SplitDictResult:
        new = {
            k: v
            for k, v in dictionary.items()
            if (k not in ignore if isinstance(ignore, Iterable) else k != ignore)
        }
        return SplitDictResult(new, dictionary, ignore)

    return split_dict


splitter = split_dict_wrapper("_")  # ignore key for serializers


def get_path_by_provider(provider: BaseProvider) -> str:
    return [
        provider_key for provider_key, prov in providers.items() if prov == provider
    ][0]


providers: Dict[str, BaseProvider] = (
    {  # k = request type (param passed in url), v = provider class
        "announcement": AnnouncementProvider,
        "blog-post": BlogPostProvider,
        "exhibit": ExhibitProvider,
        "event": EventProvider,
        "organization": OrganizationProvider,
        "flatpage": FlatPageProvider,
        "user": UserProvider,
        "tag": TagProvider,
        "term": TermProvider,
        "timetable": TimetableProvider,
        "comment": CommentProvider,
        "like": LikeProvider,
        "course": CourseProvider,
    }
)

provider_keys = providers.keys()


def get_provider(provider_name: provider_keys) -> Callable:
    """
    Gets a provider by type name.
    """
    if provider_name not in provider_keys:
        raise BadRequest(
            "Object type not found. Valid types are: " + ", ".join(providers) + "."
        )
    return providers[provider_name]


# def extend_schema_with_type(provider: BaseProvider, operation: Operations, **kwargs):
#     def decorator(view_func):
#         serializer = provider.serializers.get(operation)
#         return extend_schema(request=serializer, **kwargs)(view_func)
#     return decorator


def get_providers_by_operation(
    operation: APIObjOperations, return_provider: Optional[bool] = False
) -> List[str] | List[BaseProvider]:
    """
    returns a list of provider path names that support the given operation.

    Example:
    >>> get_providers_by_operation("single")
    ["announcement", "blog-post", "exhibit", "event", "organization", "flatpage", "user", "tag", "term", "timetable", "comment", "like", "course"]
    """
    operation = operation.lower()
    return [
        (prov if return_provider else key)
        for key, prov in providers.items()
        if getattr(prov, f"allow_{operation}", True) == True
    ]


class ObjectAPIView(generics.GenericAPIView):
    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.request.mutate = self.mutate
        self.request.kind = self.kind
        self.request.detail = self.detail
        self.provider = provider = get_provider(kwargs.pop("type"))(self.request)
        self.provider: Provider
        self.permission_classes = provider.permission_classes
        self.serializer_class = provider.serializer_class
        self.additional_lookup_fields = self._compile_lookup_fields()
        self.listing_filters = getattr(
            provider,
            "listing_filters",
            getattr(provider, "listing_filter", {"id": int, "pk": int}),
        )  # NOTE: better to have the following if after initial, but this is easier

    def _compile_lookup_fields(self) -> Set[str]:
        """
        Compiles the additional lookup fields + the two required into one clean set.
        """
        allowed_fields: List = getattr(  # the lookup fields allowed for the provider
            self.provider, "additional_lookup_fields", []
        )
        allowed_fields.extend(settings.GLOBAL_LOOKUPS)
        return set(
            allowed_fields
        )  # use a set for better memory performance & no duplicates.

    @property
    def lookup_field(self) -> str:
        lookup = (
            self.request.query_params.get("lookup", "id")
            if self.request.query_params.get("lookup") in self.additional_lookup_fields
            else "id"
        )

        field_type = self.provider.model._meta.get_field(
            lookup
        ).get_internal_type()  # get value like CharField
        if field_type in settings.LOOKUP_FIELD_REPLACEMENTS.keys():
            lookup += settings.LOOKUP_FIELD_REPLACEMENTS[field_type]
        return lookup

    def validate_lookup(self) -> None:
        """
        checks the lookup field to see if it's a valid lookup field for the provider.
        :return: NoneType
        """
        lookup = self.request.query_params.get("lookup")
        if lookup is None:
            return
        lookup = lookup or settings.GLOBAL_LOOKUPS[0]
        if lookup not in self.additional_lookup_fields:
            raise BadRequest(
                f"Invalid lookup field {lookup}. Valid fields are: {', '.join(self.additional_lookup_fields)}."
            )

    def get_object(self) -> Model | None:  # None if a 404 (obj not found)
        self.validate_lookup()
        queryset = self.get_queryset()

        q = Q()
        raw = {self.lookup_field: self.kwargs.get("lookup")}
        if self.lookup_field == "id":
            if not raw[self.lookup_field][0].isdigit():
                raise BadRequest(
                    "ID must be an integer, if you want to use a different lookup, refer to the docs for the supported lookups."
                )
        if self.lookup_field in raw:
            if (
                self.lookup_field in ("id", "pk") and raw[self.lookup_field][0] == "0"
            ):  # todo, check if needed
                # ignore 0 pk
                pass
            q |= Q(**{self.lookup_field: raw[self.lookup_field]})
        else:
            raise BadRequest("Invalid filtering - Most likely a server error")

        obj = get_object_or_404(queryset, q)
        self.check_object_permissions(self.request, obj)
        return obj

    # NOTE: dispatch() is copied from https://github.com/encode/django-rest-framework/blob/de7468d0b4c48007aed734fee22db0b79b22e70b/rest_framework/views.py
    # License for this function:
    #
    # Copyright © 2011-present, [Encode OSS Ltd](https://www.encode.io/).
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:
    #
    # * Redistributions of source code must retain the above copyright notice, this
    #   list of conditions and the following disclaimer.
    #
    # * Redistributions in binary form must reproduce the above copyright notice,
    #   this list of conditions and the following disclaimer in the documentation
    #   and/or other materials provided with the distribution.
    #
    # * Neither the name of the copyright holder nor the names of its
    #   contributors may be used to endorse or promote products derived from
    #   this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    # ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    # WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    # FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    # DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    # SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    # OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    # Note: Views are made CSRF exempt from within `as_view` as to prevent
    # accidental removal of this exemption in cases where `dispatch` needs to
    # be overridden.
    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if (request_type := request.method.lower()) in self.http_method_names:
                handler = getattr(self, request_type, self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            kwargs.pop("type")
            response = handler(request, *args, **kwargs)

        except (JSONDecodeError, UnicodeDecodeError):
            raise BadRequest("Invalid JWT, token is malformed.")
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    def get_serializer_class(self):
        return self.provider.serializer_class


class Provider(Protocol):
    allow_list: bool
    allow_new: bool
    kind: APIObjOperations
    listing_filters_ignore: List[str]

    serializers: SplitDictResult

    def __init__(self, request) -> None: ...
