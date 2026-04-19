from django import forms
from django.contrib import admin

from jazzy_tabler.widgets import JazzySelect

from .models import Category, Post


class PostInlineForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {"status": JazzySelect}


class PostInline(admin.TabularInline):
    model = Post
    form = PostInlineForm
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published_at")
    list_filter = ("category", "published_at")
    search_fields = ("title", "body")
