from django.core.management.base import BaseCommand

from demo.seed import reset, seed


class Command(BaseCommand):
    help = "Seed deterministic demo data so every admin view renders meaningfully."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-superuser",
            action="store_true",
            help="Also create an 'admin' superuser (password: DEMO_ADMIN_PASSWORD env var, default 'admin').",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the demo data first, then seed it again.",
        )

    def handle(self, *args, **options):
        run = reset if options["reset"] else seed
        summary = run(create_superuser=options["with_superuser"], verbosity=options["verbosity"])
        if summary.get("created"):
            self.stdout.write(self.style.SUCCESS(f"Seeded demo data: {summary}"))
        else:
            self.stdout.write("Demo data already present; nothing to do.")
