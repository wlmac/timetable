from __future__ import annotations

import json
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.postgres.fields import ArrayField as DjangoArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Field
from django.db.models import JSONField as DjangoJSONField
from django.db.models.fields import (  # noqa
    PositiveIntegerRelDbTypeMixin,
    SmallIntegerField,
)
from django.forms import DateField, DateInput
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field


class MonthDayFormField(DateField):
    """
    A custom form field that only allows month/day dates to be entered.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget = MonthDayInput()

    def to_python(self, value):
        """
        Parses a string value representing a month/day date into a datetime.date
        object with the current year.
        """
        if not value:
            return None
        try:
            month, day = value.split("/")
            return (
                (y := timezone.now())
                .replace(year=y.year, month=int(month), day=int(day))
                .date()
            )
        except ValueError:
            raise ValidationError(_("Invalid date format (must be MM/DD)"))

    def prepare_value(self, value) -> str:
        """
        Converts a datetime.date object into a string in the format "MM/DD".
        """
        if isinstance(value, datetime.date):
            return value.strftime("%m/%d")  # noqa
        return value


class MonthDayInput(DateInput):
    """
    A custom date input widget that only displays the month and day fields.
    """

    input_type = "text"

    def __init__(self, **kwargs):
        self.format = kwargs.pop("format", "%m/%d")
        super().__init__(**kwargs)

    def format_value(self, value):
        if isinstance(value, datetime.date):
            return value.strftime(self.format)  # noqa
        return value


class MonthDayField(models.DateField):
    """
    A custom field that allows storing a month and day without the year.
    """

    def formfield(self, **kwargs):
        defaults = {"form_class": MonthDayFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    @staticmethod
    def from_db_value(value, expression, connection):
        """
        Converts the date string stored in the database into a datetime.date object.
        """
        if value is None:
            return None
        return parse_date(value)

    def get_prep_value(self, value):
        """
        Converts a datetime.date object into a string in the format "MM/DD".
        """
        if value is None:
            return None
        return value.strftime("%m/%d")

    def to_python(self, value):
        """
        Parses a string value representing a month/day date into a datetime.date
        object with the current year.
        """
        if not value:
            return None
        try:
            month, day = value.split("/")
            return (
                (y := timezone.now())
                .replace(year=y.year, month=int(month), day=int(day))
                .date()
            )
        except ValueError:
            raise ValidationError(_("Invalid date format (must be MM/DD)"))


class PositiveOneSmallIntegerField(PositiveIntegerRelDbTypeMixin, SmallIntegerField):
    description = _("Positive small integer")

    def get_internal_type(self):
        return "PositiveSmallIntegerField"

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "min_value": 1,
                **kwargs,
            }
        )


class SetField(models.TextField):
    __token = " "

    def __init__(self, *args, **kwargs):
        super(SetField, self).__init__(*args, **kwargs)

    def to_python(self, value) -> list | tuple | None:
        if not value:
            return
        if isinstance(value, list):
            return value
        return value.split(self.__token)

    def get_db_prep_value(self, value, **kwargs):
        if not value:
            return
        if isinstance(value, str):
            return value  # allow corruption
        assert isinstance(value, list) or isinstance(
            value, tuple
        ), f"value must be list or tuple, not {type(value)}"
        return self.__token.join(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def _get_val_from_obj(self, obj):
        """
        Get the value of this field from the model instance.
        """
        return getattr(obj, self.attname)


class JSONField(DjangoJSONField):
    pass


class _TypedMultipleChoiceField(forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.pop("base_field", None)
        kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)


class ArrayField(DjangoArrayField):
    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


if "sqlite" in settings.DATABASES["default"]["ENGINE"]:

    class JSONField(Field):
        def db_type(self, connection):
            return "text"

        def from_db_value(self, value, expression, connection):
            if value is not None:
                return self.to_python(value)
            return value

        def to_python(self, value):
            if value is not None:
                try:
                    return json.loads(value)
                except (TypeError, ValueError):
                    return value
            return value

        def get_prep_value(self, value):
            if value is not None:
                return str(json.dumps(value))
            return value

        def value_to_string(self, obj):
            return self.value_from_object(obj)

    @extend_schema_field({"type": "array", "items": {"type": ["string", "number"]}})
    class ArrayField(JSONField):
        def __init__(self, base_field, size=None, **kwargs):
            """Care for DjangoArrayField's kwargs."""
            self.base_field = base_field
            self.size = size
            super().__init__(**kwargs)

        def deconstruct(self):
            """Need to create migrations properly."""
            name, path, args, kwargs = super().deconstruct()
            kwargs.update(
                {
                    "base_field": self.base_field.clone(),
                    "size": self.size,
                }
            )
            return name, path, args, kwargs

        def formfield(self, **kwargs):
            defaults = {
                "form_class": forms.MultipleChoiceField,
                "choices": self.base_field.choices,
            }
            defaults.update(kwargs)
            # Skip our parent's formfield implementation completely as we don't
            # care for it.
            # pylint:disable=bad-super-call
            return super().formfield(**defaults)


class ChoiceArrayField(ArrayField):  # credit goes to https://github.com/anyidea
    """
    A field that allows us to store an array of choices.

    Uses Django 4.2's postgres ArrayField
    and a TypeMultipleChoiceField for its formfield.

    Usage:

            choices = ChoiceArrayField(
                    models.CharField(max_length=..., choices=(...,)), blank=[...], default=[...]
            )
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": _TypedMultipleChoiceField,
            "choices": self.base_field.choices,
            "coerce": self.base_field.to_python,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't care for it.
        # pylint:disable=bad-super-call
        return super().formfield(**defaults)
