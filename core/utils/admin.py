from django.contrib.admin import ModelAdmin
from django.db.models import Q

from core.models import Tag


def generic_post_formfield_for_manytomany(
    self: ModelAdmin, db_field, request, **kwargs
):
    if db_field.name == "tags":
        kwargs["queryset"] = (
            Tag.objects.filter(
                Q(organization=None) | Q(organization__execs=request.user)
            )
            .distinct()
            .order_by("name")
        )
        if request.user.is_superuser:
            kwargs["queryset"] = Tag.objects.all().order_by("name")
    return super(self.__class__, self).formfield_for_manytomany(
        db_field, request, **kwargs
    )
