import copy
import logging
from typing import Any, Dict

from django.conf import settings
from django.templatetags.static import static

from .utils import get_admin_url, get_model_meta

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS: Dict[str, Any] = {
    # title of the window (Will default to current_admin_site.site_title)
    "site_title": None,
    # Title on the login screen (will default to current_admin_site.site_header)
    "site_header": None,
    # Title on the brand (will default to current_admin_site.site_header)
    "site_brand": None,
    # Relative path to logo for your site, used for brand on top left (must be present in static files)
    "site_logo": None,
    # Relative path to logo for your site, used for login logo (defaults to site_logo)
    "login_logo": None,
    # Logo to use when data-bs-theme is dark (defaults to login_logo)
    "login_logo_dark": None,
    # CSS classes that are applied to the logo
    "site_logo_classes": "",
    # Relative path to a favicon for your site (ideally 32x32 px)
    "site_icon": None,
    # Welcome text on the login screen
    "welcome_sign": "Welcome",
    # Copyright on the footer
    "copyright": "",
    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": None,
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    "topmenu_links": [],
    #############
    # User Menu #
    #############
    "usermenu_links": [],
    #############
    # Side Menu #
    #############
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [],
    "custom_links": {},
    # Custom icons for side menu apps/models
    # Uses Tabler Icons (ti ti-*) or FontAwesome (fas fa-*)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    "related_modal_active": False,
    #############
    # UI Tweaks #
    #############
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    ###############
    # Change view #
    ###############
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {},
    "changeform_show_buttons_below": True,
    # Add a language dropdown into the admin
    "language_chooser": False,
}


DEFAULT_UI_TWEAKS: Dict[str, Any] = {
    # Navbar style: "light" or "dark"
    "navbar": "light",
    # Make the top navbar sticky
    "navbar_fixed": True,
    # Sidebar style: "light" or "dark"
    "sidebar": "dark",
    # Make the sidebar sticky
    "sidebar_fixed": True,
    # Make the footer sticky
    "footer_fixed": False,
    # Default color scheme: "light", "dark", or "auto"
    "default_theme_mode": "light",
    # Accent color for the sidebar active item
    "accent_color": "primary",
    # Button classes
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

CHANGEFORM_TEMPLATES = {
    "single": "jazzy_tabler/includes/single.html",
    "carousel": "jazzy_tabler/includes/carousel.html",
    "collapsible": "jazzy_tabler/includes/collapsible.html",
    "horizontal_tabs": "jazzy_tabler/includes/horizontal_tabs.html",
    "vertical_tabs": "jazzy_tabler/includes/vertical_tabs.html",
}


def get_search_model_string(search_model: str) -> str:
    app, model_name = search_model.split(".")
    return "{app}.{model_name}".format(app=app, model_name=model_name.lower())


def get_settings() -> Dict[str, Any]:
    jazzy_settings = copy.deepcopy(DEFAULT_SETTINGS)
    user_jazzy_settings = getattr(settings, "JAZZY_SETTINGS", getattr(settings, "JAZZMIN_SETTINGS", {}))
    user_settings = {x: y for x, y in user_jazzy_settings.items() if y is not None}
    jazzy_settings.update(user_settings)

    if jazzy_settings["search_model"]:
        if not isinstance(jazzy_settings["search_model"], list):
            jazzy_settings["search_model"] = [jazzy_settings["search_model"]]

        jazzy_settings["search_models_parsed"] = []
        for search_model in jazzy_settings["search_model"]:
            parsed = {}
            parsed["search_url"] = get_admin_url(get_search_model_string(search_model))
            model_meta = get_model_meta(search_model)
            if model_meta:
                parsed["search_name"] = model_meta.verbose_name_plural.title()
            else:
                parsed["search_name"] = search_model.split(".")[-1] + "s"
            jazzy_settings["search_models_parsed"].append(parsed)

    if isinstance(jazzy_settings["hide_apps"], str):
        jazzy_settings["hide_apps"] = [jazzy_settings["hide_apps"]]
    jazzy_settings["hide_apps"] = [x.lower() for x in jazzy_settings["hide_apps"]]

    if isinstance(jazzy_settings["hide_models"], str):
        jazzy_settings["hide_models"] = [jazzy_settings["hide_models"]]
    jazzy_settings["hide_models"] = [x.lower() for x in jazzy_settings["hide_models"]]

    jazzy_settings["icons"] = {x.lower(): y.lower() for x, y in jazzy_settings.get("icons", {}).items()}

    jazzy_settings["site_icon"] = jazzy_settings["site_icon"] or jazzy_settings["site_logo"]
    jazzy_settings["login_logo"] = jazzy_settings["login_logo"] or jazzy_settings["site_logo"]
    jazzy_settings["login_logo_dark"] = jazzy_settings["login_logo_dark"] or jazzy_settings["login_logo"]

    jazzy_settings["changeform_format_overrides"] = {
        x.lower(): y.lower() for x, y in jazzy_settings.get("changeform_format_overrides", {}).items()
    }

    return jazzy_settings


def get_ui_tweaks() -> Dict[str, Any]:
    raw_tweaks = copy.deepcopy(DEFAULT_UI_TWEAKS)
    user_tweaks = getattr(settings, "JAZZY_UI_TWEAKS", {})
    raw_tweaks.update(user_tweaks)

    default_theme_mode = raw_tweaks.get("default_theme_mode", "light")
    if default_theme_mode not in ("light", "dark", "auto"):
        logger.warning("default_theme_mode must be light, dark, or auto; using light")
        default_theme_mode = "light"

    navbar_data_theme = "dark" if raw_tweaks.get("navbar") == "dark" else ""
    sidebar_data_theme = "dark" if raw_tweaks.get("sidebar", "dark") == "dark" else ""

    ret = {
        "raw": raw_tweaks,
        "default_theme_mode": default_theme_mode,
        "navbar_fixed": raw_tweaks.get("navbar_fixed", True),
        "navbar_data_theme": navbar_data_theme,
        "sidebar_fixed": raw_tweaks.get("sidebar_fixed", True),
        "sidebar_data_theme": sidebar_data_theme,
        "footer_fixed": raw_tweaks.get("footer_fixed", False),
        "accent_color": raw_tweaks.get("accent_color", "primary"),
        "button_classes": raw_tweaks.get("button_classes", DEFAULT_UI_TWEAKS["button_classes"]),
    }

    return ret
