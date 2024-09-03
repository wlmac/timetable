import json
from queue import LifoQueue

from django.conf import settings
from django.db.models import signals
from django.dispatch import Signal, receiver
from django.http import StreamingHttpResponse
from rest_framework import permissions, response
from rest_framework import serializers as serializers2
from rest_framework.views import APIView

from ... import models, tasks
from .. import serializers

global_notifs = Signal()


@receiver(signals.post_save, sender=models.Announcement)
def announcement_change(sender, **kwargs):
    global_notifs.send("announcement_change", orig_sender=sender, kwargs=kwargs)
    if not kwargs["created"]:
        return  # only send notifs on new announcements

    # todo add additonal checks for approve/club members ect..

    if not settings.NOTIF_DRY_RUN:
        tasks.notif_broker_announcement.delay(kwargs["instance"].id)


@receiver(signals.post_save, sender=models.BlogPost)
def blogpost_change(sender, **kwargs):
    if not kwargs["created"]:
        return  # only send notifs on new blogposts

    global_notifs.send("blogpost_change", orig_sender=sender, kwargs=kwargs)
    if not settings.NOTIF_DRY_RUN:
        tasks.notif_broker_blogpost.delay(kwargs["instance"].id)


class NotificationStream:
    def __init__(
        self,
        signal,
        serializer,
    ):
        self.signal = signal
        self.serializer = serializer
        self.q = LifoQueue()
        self.__setup()

    def __setup(self):
        self.signal.connect(self.__receive)
        self.q.put(("init", {}))

    def __del__(self):
        self.signal.disconnect(self.__receive)

    def __receive(self, sender, **kwargs):
        self.q.put((sender, kwargs))

    def __iter__(self):
        return self

    def __next__(self):
        sender, kwargs = self.q.get()
        event_name, data = self.serializer(sender, **kwargs)
        return f"event: {event_name}\n" f"data: {json.dumps(data)}\n"


def serializer(sender, signal=None, orig_sender=None, kwargs=None):
    if kwargs is None:
        kwargs = {}
    if sender == "announcement_change":
        return (
            sender,
            serializers.AnnouncementSerializer(kwargs["instance"]).data,
        )
    elif sender == "blogpost_change":
        return (
            sender,
            serializers.BlogPostSerializer(kwargs["instance"]).data,
        )
    else:
        return sender, kwargs


class NotificationsNew(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        res = StreamingHttpResponse(
            NotificationStream(
                signal=global_notifs,
                serializer=serializer,
            ),
            content_type="text/event-stream",
        )
        res["Cache-Control"] = "no-cache"
        return res


class TokenSerializer(serializers2.Serializer):
    expo_push_token = serializers2.CharField()
    options = serializers2.DictField(allow_empty=True)


class NotifToken(APIView):
    """
    Submit and delete notification push tokens.
    Supports Expo notification push tokens only for now.
    JSON object for PUT and DELETE is both of the form:
    a) {"expo_push_token": "ExponentPushToken[abc123]"}
    b) {"expo_push_token": "abc123"}
    """

    permission_classes = [permissions.IsAuthenticated]
    PREFIX = "ExponentPushToken["
    SUFFIX = "]"

    @classmethod
    def _normalize_token(cls, raw_token: str) -> str:
        if raw_token.startswith(cls.PREFIX) and raw_token.endswith(cls.SUFFIX):
            return raw_token[len(cls.PREFIX) : -len(cls.SUFFIX)]
        return raw_token

    def put(self, request, format=None):
        s = TokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        token = self._normalize_token(s.validated_data["expo_push_token"])
        request.user.expo_notif_tokens[token] = s.validated_data["options"]
        request.user.save()
        return response.Response(None)

    def delete(self, request, format=None):
        s = TokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        token = self._normalize_token(s.validated_data["expo_push_token"])
        if token in request.user.expo_notif_tokens:
            del request.user.expo_notif_tokens[token]
        request.user.save()
        return response.Response(None)
