from typing import Any

from django import forms
from django.forms.widgets import Select, SelectMultiple


class JazzySelect(Select):
    template_name = "jazzy_tabler/widgets/select.html"

    @property
    def media(self) -> forms.Media:
        return forms.Media(
            css={"all": ("vendor/select2/css/select2.min.css",)},
            js=("vendor/select2/js/select2.min.js",),
        )


class JazzySelectMultiple(SelectMultiple):
    template_name = "jazzy_tabler/widgets/select.html"

    def build_attrs(self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
        merged = dict(extra_attrs) if extra_attrs else {}
        merged["multiple"] = "multiple"
        return {**base_attrs, **merged}

    @property
    def media(self) -> forms.Media:
        return forms.Media(
            css={"all": ("vendor/select2/css/select2.min.css",)},
            js=("vendor/select2/js/select2.min.js",),
        )
