import datetime

from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ... import models
from .. import serializers, utils


class UserDetail(generics.RetrieveAPIView):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = "username__iexact"
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["user"]


class UserMe(APIView):
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["me_meta"]

    @staticmethod
    def get(request, format=None):
        serializer = serializers.UserSerializer(request.user)
        return Response(serializer.data)


class UserMeInternal(APIView):
    permission_classes = [TokenHasScope]
    required_scopes = ["me_meta", "internal"]

    @staticmethod
    def get(request, format=None):
        serializer = serializers.UserSerializerInternal(request.user)
        return Response(serializer.data)


class UserMeSchedule(APIView):
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["me_schedule"]

    def get(self, request, format=None):
        date = utils.parse_date_query_param(request)

        return Response(request.user.schedule(target_date=date))


class UserMeScheduleWeek(APIView):
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["me_schedule"]

    @staticmethod
    def get(request, format=None):
        date = utils.parse_date_query_param(request)

        return Response(
            {
                target_date.isoformat(): request.user.schedule(target_date=target_date)
                for target_date in [
                    date + datetime.timedelta(days=days) for days in range(7)
                ]
            }
        )


class UserMeTimetable(APIView):
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["me_timetable"]

    @staticmethod
    def get(request, format=None):
        current_timetable = request.user.get_current_timetable()

        if current_timetable is None:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.TimetableSerializer(current_timetable)
        return Response(serializer.data)
