from time import mktime
from wsgiref.handlers import format_date_time

from rest_framework import generics, serializers


class GenericAPIViewWithLastModified:
    def get_last_modified(self):
        raise NotImplementedError()

    def get(self, *args, **kwargs):
        resp = super().get(*args, **kwargs)
        last_modified = self.get_last_modified()
        if last_modified:
            resp["Last-Modified"] = format_date_time(mktime(last_modified.timetuple()))
        return resp


class GenericAPIViewWithDebugInfo(generics.GenericAPIView):
    def get_admin_url(self):
        return None

    def get(self, *args, **kwargs):
        resp = super().get(*args, **kwargs)
        if admin_url := self.get_admin_url():
            resp["X-Admin-URL"] = admin_url

        return resp


class ModelAbilityField(serializers.ModelField):
    def __init__(self, ability, *args, **kwargs):
        self.ability = ability
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        return super().get_attribute(instance) if self.check(instance) else None

    def check(self, instance):
        user = self.context["request"].user
        key = f"can_{self.ability}"
        if not hasattr(user, key):
            return False
        if getattr(user, key)(instance) or user.is_superuser:
            return True
        return False


class PrimaryKeyRelatedAbilityField(serializers.PrimaryKeyRelatedField):
    def __init__(self, ability, *args, **kwargs):
        self.ability = ability
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        return super().get_attribute(instance) if self.check(instance) else None

    def check(self, instance):
        user = self.context["request"].user
        key = f"can_{self.ability}"
        if not hasattr(user, key):
            return False
        if getattr(user, key)(instance) or user.is_superuser:
            return True
        return False
