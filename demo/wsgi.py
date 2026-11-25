import os
import sys
from pathlib import Path

# The repository root holds both the demo project and the jazzy_tabler package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
