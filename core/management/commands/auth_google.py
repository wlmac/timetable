from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.tasks import load_client
from pathlib import Path
import gspread 

class Command(BaseCommand):
    help = "Authenticates Google Account"

    def handle(self, *args, **options):

        SECRETS_PATH = settings.SECRETS_PATH

        CLIENT_PATH = SECRETS_PATH + "/client_secret.json"
        AUTHORIZED_PATH = SECRETS_PATH + "/authorized_user.json"
            
        client, error_msg, client_path_exists = load_client()

        if client is None:
            if not client_path_exists:
                raise CommandError(error_msg)
            elif Path(AUTHORIZED_PATH).is_file():
                user = input(f"Delete authorized_user.json located at {AUTHORIZED_PATH}? [Y/n] ")
                if user.strip().lower() not in ["yes", "y", ""]:
                    raise CommandError("Failed to authenticate")
                
                Path(AUTHORIZED_PATH).unlink()
        
            try:
                scopes = gspread.auth.READONLY_SCOPES
                
                gspread.oauth(
                    credentials_filename=CLIENT_PATH,
                    authorized_user_filename=AUTHORIZED_PATH,
                    scopes=scopes,
                )
            except Exception as e:
                raise CommandError("Failed to authenticate")

        self.stdout.write(
            self.style.SUCCESS("Successfully authenticated")
        )


        

