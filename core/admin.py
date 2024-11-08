import django.db
from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.db.models import Q, TimeField
from django.forms import Textarea
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from martor.widgets import AdminMartorWidget

from . import models
from .forms import (
    AnnouncementAdminForm,
    AnnouncementSupervisorAdminForm,
    EventAdminForm,
    OrganizationAdminForm,
    TagAdminForm,
    TagSuperuserAdminForm,
    TermAdminForm,
    UserAdminForm,
    UserCreationAdminForm,
    LateStartEventForm
)
from .models import Comment, StaffMember
from .utils.actions import (
    approve_comments,
    archive_page,
    resend_approval_email,
    reset_club_execs,
    reset_club_president,
    send_notif_singleday,
    send_test_notif,
    set_club_active,
    set_club_unactive,
    set_post_archived,
    set_post_unarchived,
    unapprove_comments,
)
from .utils.admin import generic_post_formfield_for_manytomany
from .utils.announcements import request_announcement_approval
from .utils.filters import (
    BlogPostAuthorListFilter,
    OrganizationListFilter,
    PostTypeFilter,
)

from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import path
from datetime import datetime, time
from django.core.exceptions import PermissionDenied

User = get_user_model()

# Register your models here.


class CustomTimeMixin:
    formfield_overrides = {
        TimeField: {"widget": forms.SplitDateTimeWidget},
    }

    class Media:
        js = ("js/admin-custom-times.min.js",)


class CourseInline(admin.TabularInline):
    formfield_overrides = {
        django.db.models.TextField: {"widget": Textarea(attrs={"rows": 1})},
    }
    fields = ["code", "position", "description"]
    ordering = ["code"]
    model = models.Course
    extra = 0


class StaffMemberInline(admin.StackedInline):
    model = models.StaffMember
    can_delete = False
    verbose_name_plural = "Staff Member Info"


class TermAdmin(admin.ModelAdmin):
    inlines = [
        CourseInline,
    ]
    list_display = ["name", "timetable_format", "start_date", "end_date", "is_frozen"]
    list_filter = ["timetable_format", "is_frozen"]
    ordering = ["is_frozen", "-start_date", "-end_date"]

    form = TermAdminForm


class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm
    readonly_fields = ["color"]
    list_display = ["name", "organization", "color"]
    search_fields = ["name"]

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            return TagSuperuserAdminForm
        return TagAdminForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization__execs=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organization":
            if not request.user.is_superuser:
                kwargs["queryset"] = models.Organization.objects.filter(
                    execs=request.user
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TagInline(admin.StackedInline):
    formfield_overrides = {
        django.db.models.TextField: {"widget": Textarea(attrs={"rows": 1})},
    }
    model = models.Tag
    extra = 0


class OrganizationURLInline(admin.StackedInline):
    fields = ["url"]
    model = models.OrganizationURL
    extra = 0


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "show_members", "is_open", "is_active", "owner"]
    list_filter = ["is_open", "show_members", "tags", "is_active"]
    fields = [
        "name",
        "bio",
        "extra_content",
        "slug",
        "show_members",
        "is_open",
        "is_active",
        "applications_open",
        "tags",
        "owner",
        "supervisors",
        "execs",
        "banner",
        "icon",
    ]
    autocomplete_fields = ["owner", "supervisors", "execs"]
    search_fields = ["name", "owner__username"]
    filter_horizontal = ("execs",)
    inlines = [
        TagInline,
        OrganizationURLInline,
    ]
    actions = [
        set_club_unactive,
        set_club_active,
        reset_club_president,
        reset_club_execs,
    ]
    form = OrganizationAdminForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(owner=request.user) | Q(execs=request.user)).distinct()

    def get_readonly_fields(self, request, obj=None):
        if obj is None or request.user.is_superuser or request.user == obj.owner:
            return []
        else:
            return ["owner", "supervisors", "execs", "is_active"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "supervisors" and not request.user.is_superuser:
            kwargs["queryset"] = models.User.objects.filter(is_teacher=True).order_by(
                "username"
            )
        if db_field.name == "execs":
            kwargs["queryset"] = models.User.objects.all().order_by("username")
        if db_field.name == "tags":
            kwargs["queryset"] = models.Tag.objects.filter(
                Q(organization=None) | Q(organization__execs=request.user)
            ).distinct()
            if request.user.is_superuser:
                kwargs["queryset"] = models.Tag.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class PostAdmin(admin.ModelAdmin):
    readonly_fields = ["like_count", "save_count", "comments"]
    fields = ["like_count", "save_count", "comments"]

    def like_count(self, obj) -> int:
        return obj.like_count

    like_count.short_description = "Like count"

    def save_count(self, obj) -> int:
        saves = User.objects.filter(saved_announcements=obj).count()
        if saves is not None:
            return saves
        return 0

    save_count.short_description = "Save Count"

    def comments(self, obj):
        objs = list(
            map(
                lambda obj: '<a target="_blank" href="/admin/core/comment/%s">%s</a>'
                % (obj.pk, obj.body[:10]),
                obj.comments.all(),
            )
        )
        return mark_safe(",".join(objs))

    comments.short_description = "Comments"

    class Meta:
        abstract = True


class AnnouncementAdmin(CustomTimeMixin, PostAdmin):
    list_display = ["__str__", "organization", "status"]
    list_filter = [OrganizationListFilter, "status"]
    ordering = ["-show_after"]
    actions = [resend_approval_email]
    empty_value_display = "Not specified."
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return (
            qs.filter(
                Q(organization__supervisors=request.user)
                | Q(organization__execs=request.user)
            )
            .distinct()
            .filter(organization__is_active=True)
        )

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = (
            AnnouncementSupervisorAdminForm
            if request.user.is_superuser or request.user.is_teacher
            else AnnouncementAdminForm
        )
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return PostAdmin.readonly_fields

        all_fields = [
            "organization",
            "author",
            "title",
            "body",
            "tags",
            "is_public",
            "status",
            "rejection_reason",
            "supervisor",
        ]
        status_idx = ["d", "p", "a", "r"].index(obj.status)

        fields = set(all_fields)
        fields_matrix = [
            [
                {
                    "author",
                    "organization",
                    "title",
                    "tags",
                    "is_public",
                    "supervisor",
                },
                {
                    "author",
                    "organization",
                    "title",
                    "tags",
                    "is_public",
                    "supervisor",
                },
                {
                    "author",
                    "organization",
                    "title",
                    "body",
                    "tags",
                    "show_after",
                    "is_public",
                    "status",
                    "supervisor",
                },
                {
                    "author",
                    "organization",
                    "title",
                    "body",
                    "tags",
                    "is_public",
                    "status",
                    "rejection_reason",
                    "supervisor",
                },
            ],
            [
                {"author", "organization", "supervisor"},
                {"author", "organization", "status", "supervisor"},
                {
                    "author",
                    "organization",
                    "status",
                    "show_after",
                    "supervisor",
                },
                {
                    "author",
                    "organization",
                    "status",
                    "supervisor",
                    "rejection_reason",
                },
            ],
        ]

        if request.user in obj.organization.supervisors.all():
            fields.intersection_update(fields_matrix[0][status_idx])
        if request.user in obj.organization.execs.all():
            fields.intersection_update(fields_matrix[1][status_idx])

        fields = list(fields)
        fields.sort(key=lambda x: all_fields.index(x))
        fields.extend(PostAdmin.readonly_fields)

        return fields

    def get_fields(self, request, obj=None):
        all_fields = [
            "organization",
            "author",
            "title",
            "body",
            "tags",
            "show_after",
            "is_public",
            "status",
            "rejection_reason",
            "supervisor",
        ]

        fields = set(all_fields)
        fields.difference_update(self.get_exclude(request, obj))

        fields = list(fields)
        fields.sort(key=lambda x: all_fields.index(x))
        if obj and obj.pk:
            fields.extend(PostAdmin.fields)

        return fields

    def get_exclude(self, request, obj=None):
        if request.user.is_superuser:
            return {}

        if obj is None:
            return {"author", "supervisor", "rejection_reason"}

        status_idx = ["d", "p", "a", "r"].index(obj.status)

        fields = {
            "title",
            "body",
            "tags",
            "organization",
            "is_public",
            "supervisor",
            "status",
            "rejection_reason",
        }
        fields_matrix = [
            [{"supervisor"}, {"rejection_reason"}, {}],
            [{"supervisor", "rejection_reason"}, {"rejection_reason"}, {}],
        ]

        if request.user in obj.organization.supervisors.all():
            fields.intersection_update(fields_matrix[0][status_idx])
        if request.user in obj.organization.execs.all():
            fields.intersection_update(fields_matrix[1][status_idx])

        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organization":
            if request.user.is_superuser:
                kwargs["queryset"] = models.Organization.objects.all().order_by("name")
            else:
                kwargs["queryset"] = (
                    models.Organization.objects.filter(
                        Q(supervisors=request.user) | Q(execs=request.user)
                    )
                    .distinct()
                    .order_by("name")
                )
        elif (
            db_field.name in {"author", "supervisor"} and not request.user.is_superuser
        ):
            orgs = models.Organization.objects.filter(
                Q(supervisors=request.user) | Q(execs=request.user)
            )
            qs_set = True
            if db_field.name == "author":
                kwargs["queryset"] = models.User.objects.filter(
                    organizations_leading__in=orgs,
                )
                if request.user.is_superuser:
                    kwargs["queryset"] = models.User.objects.all()
            elif db_field.name == "supervisor":
                kwargs["queryset"] = models.User.objects.filter(
                    organizations_supervising__in=orgs,
                )
            else:
                qs_set = False
            if qs_set:
                kwargs["queryset"] = kwargs["queryset"].distinct().order_by("username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return generic_post_formfield_for_manytomany(self, db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if (
            obj is not None
            and obj.status not in ("d", "p")
            and not request.user.is_superuser
            and request.user in obj.organization.supervisors.all()
            and request.user not in obj.organization.execs.all()
        ):
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user

        notify_supervisors = False

        if not request.user.is_superuser:
            if request.user in obj.organization.supervisors.all():
                obj.supervisor = request.user
                if obj.status not in ("d", "p") and request.user != obj.author:
                    # Notify author
                    self.message_user(
                        request,
                        f"Successfully marked announcement as {obj.get_status_display()}.",
                    )
            else:
                if (not change) or obj.status not in ("d", "p"):
                    notify_supervisors = True

                    self.message_user(
                        request, "Successfully sent announcement for review."
                    )
                obj.status = "p" if obj.status != "d" else "d"

        super().save_model(request, obj, form, change)

        if notify_supervisors:
            request_announcement_approval(obj)


class BlogPostAdmin(PostAdmin):
    list_display = ["title", "author", "is_published", "views", "is_archived"]
    list_filter = [BlogPostAuthorListFilter, "is_published", "is_archived"]
    ordering = ["-show_after", "views"]
    fields = [
        "author",
        "title",
        "slug",
        "views",
        "body",
        "featured_image",
        "featured_image_description",
        "show_after",
        "tags",
        "is_published",
    ]
    readonly_fields = PostAdmin.readonly_fields
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }
    actions = [set_post_archived, set_post_unarchived]

    def get_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.fields + PostAdmin.fields
        return self.fields

    def get_changeform_initial_data(self, request):
        return {"author": request.user.pk}

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return generic_post_formfield_for_manytomany(self, db_field, request, **kwargs)


class ExhibitAdmin(PostAdmin):
    list_display = ["title", "author", "is_published"]
    list_filter = [BlogPostAuthorListFilter, "is_published"]
    ordering = ["-show_after"]
    fields = [
        "author",
        "title",
        "slug",
        "content",
        "content_description",
        "show_after",
        "tags",
        "is_published",
    ] + PostAdmin.fields
    readonly_fields = PostAdmin.readonly_fields
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }

    def get_changeform_initial_data(self, request):
        return {"author": request.user.pk}

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["queryset"] = (
                models.Tag.objects.filter(Q(organization=None))
                .distinct()
                .order_by("name")
            )
            if request.user.is_superuser:
                kwargs["queryset"] = models.Tag.objects.all().order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class EventAdmin(CustomTimeMixin, admin.ModelAdmin):
    list_display = ["name", "organization", "start_date", "end_date"]
    list_filter = [OrganizationListFilter]
    ordering = ["-start_date", "-end_date"]
    search_fields = ["name"]
    change_list_template = 'admin/change_list_buttons.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['buttons'] = [
            {
                'name': 'Add Late Start',
                'url': reverse('admin:late_start'),
            },
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):  
        return [
            path(
                "createLateStart/",
                self.admin_site.admin_view(self.late_start_view),
                name="late_start"
            ),
            *super().get_urls(),
        ]

    def late_start_view(self, request):

        if not request.user.has_perm('core.add_event'):
            raise PermissionDenied()
        
        url = request.get_full_path()
        
        context = dict(
            self.admin_site.each_context(request),
            form=LateStartEventForm,
            url=url,
            title='Add Late Start',
            media=LateStartEventForm().media
        )

        if request.method == 'POST':
            form = LateStartEventForm(request.POST)
            if form.is_valid():
                start_date_value = form.cleaned_data.get('start_date')
                start_date = datetime.combine(start_date_value, time(hour=10))
                end_date = datetime.combine(start_date_value, time(hour=10, second=1))

                data = {
                    'name': 'Late Start',
                    'term': models.Term.get_current(start_date),
                    'schedule_format': 'late-start',
                    'start_date': start_date,
                    'end_date': end_date
                }

                try:
                    data["organization"] = models.Organization.objects.get(name='SAC')
                except models.Organization.DoesNotExist:

                    if not request.user.has_perm('core.add_organization'):
                        raise PermissionDenied()

                    earliest_superuser = models.User.objects.filter(is_superuser=True).earliest("date_joined")

                    organization_data = {
                        'bio': 'WLMAC Student Activity Council',
                        'is_open': False,
                        'name': 'SAC',
                        'slug': 'wlmac',
                        'owner': earliest_superuser
                    }

                    sac_org = models.Organization.objects.create(**organization_data)
                    sac_org.execs.add(earliest_superuser)
                    sac_org.save()

                    data["organization"] = sac_org

                models.Event.objects.create(**data)
                return redirect("/admin/core/event")
            else:
                context['form'] = form 
                return TemplateResponse(request, "admin/custom_form.html", context)
        else:
            return TemplateResponse(request, "admin/custom_form.html", context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization__execs=request.user)

    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return {"schedule_format", "is_instructional"}

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs["form"] = EventAdminForm
        return super().get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        return generic_post_formfield_for_manytomany(self, db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organization":
            if not request.user.is_superuser:
                kwargs["queryset"] = models.Organization.objects.filter(
                    execs=request.user
                ).order_by("name")
            if request.user.is_superuser:
                kwargs["queryset"] = models.Organization.objects.all().order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if (
            obj is not None
            and (not request.user.is_superuser)
            and (request.user not in obj.organization.execs.all())
        ):
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not all(
            map(
                lambda date: obj.term.start_datetime()
                <= date
                <= obj.term.end_datetime(),
                [obj.start_date, obj.end_date],
            )
        ):
            self.message_user(
                request,
                _("Event timeframe does not overlap term timeframe."),
                level=messages.ERROR,
            )
        super().save_model(request, obj, form, change)


class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "is_superuser", "is_staff", "is_teacher"]
    list_filter = [
        "is_superuser",
        "is_staff",
        "is_teacher",
        "groups",
        "graduating_year",
        "is_deleted",
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "saved_blogs__title",
        "saved_announcements__title",
    ]
    actions = [send_test_notif, send_notif_singleday]
    form = UserAdminForm
    add_form = UserCreationAdminForm

    def get_inline_instances(self, request, obj=None):
        if obj and StaffMember.objects.filter(user=obj).exists():
            # Add StaffMemberInline if the user has a related StaffMember
            return [StaffMemberInline(self.model, self.admin_site)]
        return []

    def has_view_permission(self, request, obj=None):
        if obj is None and (
            request.user.organizations_owning.exists()
            or request.user.organizations_leading.exists()
        ):
            return True

        return super().has_view_permission(request, obj)

    def has_module_permission(self, request):
        return request.user.has_perm("core.view_user") or request.user.is_superuser


class TimetableAdmin(admin.ModelAdmin):
    list_display = ["__str__", "term"]
    list_filter = ["term"]


class CustomFlatPageAdmin(FlatPageAdmin):
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }
    actions = [archive_page]
    fieldsets = (
        (None, {"fields": ("url", "title", "content", "sites")}),
        (
            _("Advanced options"),
            {
                "classes": ("collapse",),
                "fields": (
                    "registration_required",
                    "template_name",
                ),
            },
        ),
    )


class RaffleAdmin(admin.ModelAdmin):
    list_display = ["__str__", "open_start", "open_end"]


class CommentAdmin(admin.ModelAdmin):
    formfield_overrides = {
        django.db.models.TextField: {"widget": AdminMartorWidget},
    }
    list_display = ["author", "content_object", "created_at"]
    search_fields = ["author__username", "body"]
    actions = [approve_comments, unapprove_comments]
    readonly_fields = ["created_at", "likes"]
    list_filter = ["live", PostTypeFilter]
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = "created_at"

    @staticmethod
    def likes(obj: Comment):
        return obj.like_count

    def get_queryset(self, request):
        return Comment.objects.filter(author__isnull=False).order_by("-created_at")

    def content_object(self, obj):
        url = reverse(
            f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
            args=[obj.object_id],
        )
        return format_html('<a href="{}">{}</a>', url, str(obj.content_object))

    content_object.short_description = "Associated Post"


admin.site.register(User, UserAdmin)
admin.site.register(models.Timetable, TimetableAdmin)
admin.site.register(models.Term, TermAdmin)
admin.site.register(models.Course)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.Announcement, AnnouncementAdmin)
admin.site.register(models.BlogPost, BlogPostAdmin)
admin.site.register(models.Exhibit, ExhibitAdmin)
# admin.site.register(models.Comment, CommentAdmin) atm it's not used, so we don't need it
admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Event, EventAdmin)
admin.site.register(models.Raffle, RaffleAdmin)
admin.site.register(models.StaffMember)

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, CustomFlatPageAdmin)

admin.site.site_header = "Metropolis administration"
admin.site.site_title = "Metropolis admin"
