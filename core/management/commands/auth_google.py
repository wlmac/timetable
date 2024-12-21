from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import gspread 

class Command(BaseCommand):
    help = "Authenticates Google Account"

    def handle(self, *args, **options):

        SECRETS_PATH = settings.SECRETS_PATH

        CLIENT_PATH = SECRETS_PATH + "/client_secret.json"
        AUTHORIZED_PATH = SECRETS_PATH + "/authorized_user.json"

        scopes = gspread.auth.READONLY_SCOPES

        if not Path(settings.SECRETS_PATH).is_dir():
            raise CommandError(f"{SECRETS_PATH} directory does not exist")
        
        if not Path(CLIENT_PATH).is_file():
            raise CommandError(f"{CLIENT_PATH} file does not exist")
        
        try:
            gspread.oauth(
                credentials_filename=CLIENT_PATH,
                authorized_user_filename=AUTHORIZED_PATH,
                scopes=scopes,
            )

            self.stdout.write(
                self.style.SUCCESS("Successfully authenticated")
            )

        except Exception as e:
            raise CommandError("Failed to authenticate")
