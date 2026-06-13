from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path


def preview_404(request):
    context = {**admin.site.each_context(request), "title": "Page not found"}
    return TemplateResponse(request, "admin/404.html", context, status=404)


def preview_500(request):
    context = {**admin.site.each_context(request), "title": "Server error"}
    return TemplateResponse(request, "admin/500.html", context, status=500)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("preview/404/", preview_404, name="preview_404"),
    path("preview/500/", preview_500, name="preview_500"),
]
