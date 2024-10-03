from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.base import RedirectView
from django.views.generic.edit import UpdateView

from .. import models
from . import mixins


class ProfileRedirect(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = False
    pattern_name = "profile_detail"

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        return reverse(self.pattern_name, args=[user.username])


class Profile(LoginRequiredMixin, DetailView, mixins.TitleMixin):
    model = models.User
    context_object_name = "profile"
    template_name = "core/profile/detail.html"

    def get_slug_field(self):
        return "username"

    def get_title(self):
        return f"User {self.get_object().username}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj_org_exists = context["object"].organizations.exists()
        if context["object"] == self.request.user and obj_org_exists:
            context["following"] = context["object"].organizations.all()
        elif obj_org_exists:
            context["following"] = context["object"].organizations.filter(
                show_members=True
            )
        return context


class ProfileUpdate(LoginRequiredMixin, UpdateView, mixins.TitleMixin):
    model = models.User
    fields = ["bio", "first_name", "last_name", "graduating_year"]
    template_name = "core/profile/update.html"
    success_url = reverse_lazy("profile_redirect")
    title = "Update Profile"
    context_object_name = "profile"

    def get_object(self):
        return self.request.user
