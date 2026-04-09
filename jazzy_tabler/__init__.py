from importlib.metadata import version as package_version

try:
    version = package_version("django-jazzy-tabler")
except Exception:
    version = "0.0.0"
