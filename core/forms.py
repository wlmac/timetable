from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm as ContribUserChangeForm
from django.contrib.auth.forms import (
    AdminUserCreationForm as ContribAdminUserCreationForm,
)
from django.utils import timezone
from django_select2 import forms as s2forms
from martor.widgets import AdminMartorWidget

from core import models
from core.views.mixins import CaseInsensitiveUsernameMixin


class MetropolisSignupForm(SignupForm, CaseInsensitiveUsernameMixin):
    first_name = forms.CharField(
        max_length=30,
        label="First Name",
        widget=forms.TextInput(attrs={"type": "text", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Last Name",
        widget=forms.TextInput(attrs={"type": "text", "autocomplete": "family-name"}),
    )
    graduating_year = forms.ChoiceField(
        choices=models.graduating_year_choices, required=False
    )
    field_order = [
        "email",
        "username",
        "first_name",
        "last_name",
        "graduating_year",
        "password1",
        "password2",
    ]

    def save(self, request):
        user = super(MetropolisSignupForm, self).save(request)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.graduating_year = self.cleaned_data["graduating_year"]
        if self.cleaned_data["email"].endswith(settings.TEACHER_EMAIL_SUFFIX):
            user.is_teacher = True
        user.save()
        return user

    def __init__(self, *args, **kwargs):
        super(MetropolisSignupForm, self).__init__(*args, **kwargs)
        del self.fields["email"].widget.attrs["placeholder"]
        del self.fields["username"].widget.attrs["placeholder"]
        del self.fields["password1"].widget.attrs["placeholder"]
        del self.fields["password2"].widget.attrs["placeholder"]

    def clean_email(self):
        email = super(MetropolisSignupForm, self).clean_email()
        if not (
            email.endswith(settings.STUDENT_EMAIL_SUFFIX)
            or email.endswith(settings.TEACHER_EMAIL_SUFFIX)
        ):
            raise forms.ValidationError("A TDSB email must be used.")
        return email

    def clean_graduating_year(self):
        graduating_year = self.cleaned_data["graduating_year"]
        if graduating_year == "":
            return None
        return graduating_year


class AddTimetableSelectTermForm(forms.Form):
    term = forms.ModelChoiceField(queryset=models.Term.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(AddTimetableSelectTermForm, self).__init__(*args, **kwargs)
        self.fields["term"].queryset = (
            models.Term.objects.filter(
                end_date__gte=timezone.now() - settings.TERM_GRACE_PERIOD
            )
            .exclude(timetables__owner=user)
            .order_by("-start_date")
        )


class SelectCoursesWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "code__icontains",
    ]


class TimetableSelectCoursesForm(forms.ModelForm):
    class Meta:
        model = models.Timetable
        fields = ["courses"]
        widgets = {
            "courses": SelectCoursesWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "width": "100%",
                    "data-placeholder": "Start typing course code...",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        if kwargs["instance"] is not None:
            self.term = kwargs["instance"].term
        else:
            self.term = kwargs.pop("term")
        super(TimetableSelectCoursesForm, self).__init__(*args, **kwargs)
        self.fields["courses"].queryset = models.Course.objects.filter(
            term=self.term
        ).order_by("code")

    def clean(self):
        courses = self.cleaned_data["courses"]
        if (
            courses.count()
            > settings.TIMETABLE_FORMATS[self.term.timetable_format]["courses"]
        ):
            raise forms.ValidationError(
                f'There are only {settings.TIMETABLE_FORMATS[self.term.timetable_format]["courses"]} courses in this term.'
            )
        position_set = set()
        for i in courses:
            if i.position in position_set:
                raise forms.ValidationError(
                    "There are two or more conflicting courses."
                )
            else:
                position_set.add(i.position)


class AddCourseForm(forms.ModelForm):
    position = forms.ChoiceField(widget=forms.RadioSelect())

    class Meta:
        model = models.Course
        fields = ["code", "position"]

    def __init__(self, *args, **kwargs):
        self.term = kwargs.pop("term")
        super(AddCourseForm, self).__init__(*args, **kwargs)

        self.fields["position"].label = settings.TIMETABLE_FORMATS[
            self.term.timetable_format
        ]["question"]["prompt"]
        self.fields["position"].choices = settings.TIMETABLE_FORMATS[
            self.term.timetable_format
        ]["question"]["choices"]

        term_courses = self.term.courses.order_by("?")
        if term_courses:
            self.fields["code"].widget.attrs["placeholder"] = (
                f"Ex. {term_courses[0].code}"
            )

        self.position_set = list(
            settings.TIMETABLE_FORMATS[self.term.timetable_format]["positions"]
        )
        self.position_set.sort()

    def clean_code(self):
        code = self.cleaned_data["code"]
        courses = self.term.courses.filter(code=code)
        if courses:
            raise forms.ValidationError(
                "A course with the same code exists for the selected term."
            )
        return code

    def clean_position(self):
        position = int(self.cleaned_data["position"])
        if position not in self.position_set:
            raise forms.ValidationError(
                "Must be one of " + ", ".join([str(i) for i in self.position_set]) + "."
            )
        return position


class OrganizationAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            "extra_content": AdminMartorWidget,
        }

    def clean(self):
        cleaned_data = super().clean()
        owner = cleaned_data.get("owner")
        execs = cleaned_data.get("execs")

        if owner is not None and execs is not None and owner not in execs:
            raise forms.ValidationError({"execs": "The owner must also be an exec."})


class TermAdminForm(forms.ModelForm):
    timetable_format = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(TermAdminForm, self).__init__(*args, **kwargs)
        self.fields["timetable_format"].choices = [
            (timetable_format, timetable_format)
            for timetable_format in settings.TIMETABLE_FORMATS
        ]


class EventAdminForm(forms.ModelForm):
    schedule_format = forms.ChoiceField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(EventAdminForm, self).__init__(*args, **kwargs)
        timetable_configs = settings.TIMETABLE_FORMATS

        self.fields["schedule_format"].initial = "default"
        self.fields["term"].initial = models.Term.get_current()
        self.fields["is_instructional"].disabled = True

        if "instance" in kwargs and kwargs["instance"] is not None:
            instance = kwargs["instance"]
            self.fields["schedule_format"].choices = [
                (timetable_format, timetable_format)
                for timetable_format in timetable_configs[
                    instance.term.timetable_format
                ]["schedules"]
            ]
        else:
            schedule_format_set = set()
            for timetable_config in timetable_configs.values():
                schedule_format_set.update(set(timetable_config["schedules"].keys()))
            self.fields["schedule_format"].choices = [
                (schedule_format, schedule_format)
                for schedule_format in schedule_format_set
            ]

    def clean(self):
        cleaned_data = super().clean()
        term = cleaned_data.get("term")
        schedule_format = cleaned_data.get("schedule_format")

        if not term:
            raise TypeError("term not defined")

        timetable_configs = settings.TIMETABLE_FORMATS
        if schedule_format not in timetable_configs[term.timetable_format]["schedules"]:
            raise forms.ValidationError(
                f'Schedule format "{schedule_format}" is not a valid day schedule in Term {term.name}.'
            )


class TagSuperuserAdminForm(forms.ModelForm):
    class Meta:
        model = models.Tag
        fields = "__all__"


class TagAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_organization(self):
        if self.cleaned_data["organization"] is None:
            raise forms.ValidationError("Tags must have an organization.")
        return self.cleaned_data["organization"]

    class Meta:
        model = models.Tag
        fields = "__all__"


class AnnouncementAdminForm(forms.ModelForm):
    status = forms.ChoiceField(
        widget=forms.Select(),
        choices=models.announcement_status_initial_choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "status" in self.fields:
            self.fields["status"].initial = "d"


class AnnouncementSupervisorAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "status" in self.fields:
            self.fields["status"].initial = "d"


class UserAdminForm(CaseInsensitiveUsernameMixin, ContribUserChangeForm):
    expo_notif_tokens = forms.JSONField(required=False)


class UserCreationAdminForm(CaseInsensitiveUsernameMixin, ContribAdminUserCreationForm):
    pass
