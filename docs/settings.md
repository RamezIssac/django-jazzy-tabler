# Settings protocol

django-jazzy-tabler is configured through two optional dicts in `settings.py`:

- **`JAZZY_SETTINGS`** — content & behavior (branding, menus, icons, changeform layout, …)
- **`JAZZY_UI_TWEAKS`** — look & feel (navbar/sidebar style, theme mode, accent color, button classes)

Everything is optional; every key has a default. `jazzy_tabler` must be listed **before** `django.contrib.admin` in `INSTALLED_APPS` so its templates win.

## Jazzmin compatibility & fallback

The settings surface is intentionally [django-jazzmin](https://github.com/farridav/django-jazzmin)-compatible:

- If `JAZZY_SETTINGS` is **not defined at all**, the theme reads **`JAZZMIN_SETTINGS`** as a fallback — so you can flip between jazzmin and jazzy-tabler by swapping `INSTALLED_APPS` entries.
- If `JAZZY_SETTINGS` **is** defined (even empty), it wins and `JAZZMIN_SETTINGS` is ignored.
- Keys set to `None` are dropped and the defaults apply. Unknown keys are harmless (ignored).
- Only the keys documented below are honored — jazzmin keys that make no sense for Tabler (e.g. AdminLTE skin classes) are silently ignored.

## `JAZZY_SETTINGS` reference

### Branding

| Key | Default | Notes |
|---|---|---|
| `site_title` | admin site's `site_title` | Browser tab title suffix. |
| `site_header` | admin site's `site_header` | Heading on the login screen. |
| `site_brand` | `site_header` | Brand text next to the logo in the sidebar. |
| `site_logo` | `None` | Static-file path of the sidebar brand logo, e.g. `"app/img/logo.svg"`. |
| `site_logo_classes` | `""` | Extra CSS classes for the brand `<img>`. |
| `site_icon` | `site_logo` | Static-file path of the favicon (ideally 32×32). |
| `login_logo` | `site_logo` | Logo on the login screen. |
| `login_logo_dark` | `login_logo` | Login logo used when dark mode is active. |
| `welcome_sign` | `"Welcome"` | Heading text on the login screen. |
| `copyright` | `""` | Footer copyright holder. |

### Top navbar

| Key | Default | Notes |
|---|---|---|
| `search_model` | `None` | `"app.Model"` or a list of them. Renders a global search box in the navbar that submits to that model's changelist. Omit to hide the box. |
| `topmenu_links` | `[]` | List of link dicts (see [Menu links](#menu-links)). Rendered in the top navbar; `app` entries become dropdowns. |

### User menu (top right)

| Key | Default | Notes |
|---|---|---|
| `usermenu_links` | `[]` | List of link dicts appended to the account dropdown (after “Change password” / “Log out”). `app` entries are not supported here. |
| `user_avatar` | `None` | Field name on the user model (`ImageField`, `URLField` or `CharField`) or a callable receiving the user and returning a URL. Used for the avatar in the navbar/sidebar. |

### Sidebar

| Key | Default | Notes |
|---|---|---|
| `show_sidebar` | `True` | `False` removes the sidebar entirely (top navbar only). |
| `navigation_expanded` | `True` | Reserved (jazzmin compat; accepted but currently unused — collapse state is controlled per-user via the sidebar toggle cookie). |
| `hide_apps` | `[]` | App labels to hide from the sidebar, e.g. `["auth"]`. Accepts a single string too; case-insensitive. |
| `hide_models` | `[]` | Models to hide, as `"app.model"` (case-insensitive), e.g. `["auth.group"]`. |
| `order_with_respect_to` | `[]` | Reorder sidebar apps/models, e.g. `["blog", "blog.post", "auth"]`. Unlisted items keep their relative order. |
| `custom_links` | `{}` | Extra sidebar entries per app: `{"blog": [link, ...]}` (see [Menu links](#menu-links)). Custom apps not in `INSTALLED_APPS` get their own sidebar group. |
| `icons` | auth defaults below | Icon per app or model: `{"auth": "fas fa-users-cog", "auth.user": "fas fa-user", "blog.post": "fas fa-newspaper"}`. Keys are lower-cased (`auth.user`, not `auth.User`). Any [FontAwesome Free](https://fontawesome.com/search?ic=free) class (`fas fa-*`) works. |
| `default_icon_parents` | `"fas fa-chevron-circle-right"` | Fallback icon for apps. |
| `default_icon_children` | `"fas fa-circle"` | Fallback icon for models. |

Default `icons`:

```python
{
    "auth": "fas fa-users-cog",
    "auth.user": "fas fa-user",
    "auth.group": "fas fa-users",
}
```

### Menu links

`topmenu_links`, `usermenu_links` and `custom_links` entries are dicts with **one of** `url` / `model` / `app`:

```python
{"name": "Acme site", "url": "https://acme.example", "icon": "fas fa-globe", "new_window": True}
{"name": "Posts", "model": "blog.Post"}                                  # links to the changelist
{"name": "Blog", "app": "blog"}                                          # dropdown of the app's models (top menu only)
{"name": "Staff only", "url": "admin:index", "permissions": ["auth.add_user"]}
```

- `url` may be an absolute/relative URL **or a named URL** (reversed for you).
- `permissions` (list): the link renders only if the user has **all** of them.
- `icon` and `new_window` are optional.

### Change form

| Key | Default | Notes |
|---|---|---|
| `changeform_format` | `"horizontal_tabs"` | How fieldsets/inlines are laid out. One of `"single"`, `"horizontal_tabs"`, `"vertical_tabs"`, `"carousel"`, `"collapsible"`. |
| `changeform_format_overrides` | `{}` | Per-model override: `{"auth.user": "collapsible", "blog.post": "single"}` (keys case-insensitive). |
| `changeform_show_buttons_below` | `True` | `True`: submit row in a card footer below the form. `False`: submit row in a sticky right-hand actions sidebar. |
| `related_modal_active` | `False` | Reserved: render related-object add/change popups as modals instead of pop-up windows. |
| `related_view_links_to_view` | `True` | The FK “view” icon opens the object's **view** page; `False` routes it to the change form (classic behavior). |
| `hide_number_spinners` | `True` | Hides the browser's up/down arrows on `<input type="number">`. |

### Extras

| Key | Default | Notes |
|---|---|---|
| `custom_css` | `None` | Static-file path of an extra stylesheet loaded after the theme's. |
| `custom_js` | `None` | Static-file path of an extra script loaded at the end of `<body>`. |
| `language_chooser` | `False` | Show a language dropdown in the navbar (needs `set_language` in your URLconf and `LANGUAGES` configured). |
| `show_ui_builder` | `False` | Reserved (jazzmin compat; no live UI builder is shipped). |

## `JAZZY_UI_TWEAKS` reference

| Key | Default | Allowed values |
|---|---|---|
| `navbar` | `"light"` | `"light"` / `"dark"` — top navbar style. |
| `navbar_fixed` | `True` | bool — top navbar stays sticky. |
| `sidebar` | `"dark"` | `"light"` / `"dark"` — sidebar style. |
| `sidebar_fixed` | `True` | bool — sidebar stays sticky. |
| `footer_fixed` | `False` | bool — sticky footer. |
| `default_theme_mode` | `"light"` | `"light"` / `"dark"` / `"auto"` (follows `prefers-color-scheme`). Users can always toggle; their choice is remembered in `localStorage`. |
| `accent_color` | `"primary"` | Any Tabler color name: `"primary"`, `"azure"`, `"blue"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`. Colors the sidebar's active item. |
| `button_classes` | see below | Maps semantic actions to button CSS classes. |

Default `button_classes`:

```python
{
    "primary": "btn-primary",
    "secondary": "btn-secondary",
    "info": "btn-info",
    "warning": "btn-warning",
    "danger": "btn-danger",
    "success": "btn-success",
}
```

## Full example

```python
JAZZY_SETTINGS = {
    "site_title": "Acme Admin",
    "site_header": "Acme",
    "site_brand": "Acme",
    "site_logo": "acme/img/logo.svg",
    "login_logo": "acme/img/login-logo.svg",
    "login_logo_dark": "acme/img/login-logo-dark.svg",
    "site_icon": "acme/img/favicon-32.png",
    "welcome_sign": "Welcome back",
    "copyright": "Acme Inc",
    "search_model": ["blog.Post", "auth.User"],
    "user_avatar": "avatar",
    "topmenu_links": [
        {"name": "View site", "url": "/", "icon": "fas fa-globe", "new_window": True},
        {"app": "blog"},
    ],
    "usermenu_links": [
        {"name": "Status page", "url": "https://status.acme.example", "new_window": True},
    ],
    "hide_apps": [],
    "hide_models": ["auth.Group"],
    "order_with_respect_to": ["blog", "blog.post", "auth"],
    "custom_links": {
        "blog": [{"name": "Import posts", "url": "admin:blog_post_import", "icon": "fas fa-file-import"}],
    },
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "blog": "fas fa-newspaper",
        "blog.post": "fas fa-file-alt",
    },
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible"},
    "changeform_show_buttons_below": True,
    "custom_css": "acme/css/admin-extra.css",
    "custom_js": "acme/js/admin-extra.js",
}

JAZZY_UI_TWEAKS = {
    "navbar": "light",
    "sidebar": "dark",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "default_theme_mode": "auto",
    "accent_color": "azure",
}
```
