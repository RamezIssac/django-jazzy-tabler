from django.core.management.base import BaseCommand

from demo.admin_inventory import inventory_as_json


class Command(BaseCommand):
    help = "Print the admin URL inventory as JSON (consumed by the screenshot matrix)."

    def handle(self, *args, **options):
        self.stdout.write(inventory_as_json())
