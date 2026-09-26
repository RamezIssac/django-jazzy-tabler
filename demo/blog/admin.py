from django import forms
from django.contrib import admin

from jazzy_tabler.widgets import JazzySelect

from .models import Author, Category, Comment, Post, Tag


class PostInlineForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {"status": JazzySelect}


class PostInline(admin.TabularInline):
    """Tabular inline: exercises the tabular inline template + select2 inside inlines."""

    model = Post
    form = PostInlineForm
    fields = ("title", "status", "is_featured", "published_at")
    extra = 1


class CommentInline(admin.StackedInline):
    """Stacked inline: exercises the stacked inline template."""

    model = Comment
    fields = ("author_name", "text")
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    inlines = [PostInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "email")
    search_fields = ("name", "email")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "is_featured", "views", "published_at")
    list_filter = ("status", "is_featured", "category", "published_at")
    search_fields = ("title", "body")
    date_hierarchy = "published_at"
    autocomplete_fields = ["category"]
    filter_horizontal = ["tags"]
    list_per_page = 10
    inlines = [CommentInline]
