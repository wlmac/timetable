# Metropolis (Backend)
Make sure you have python 3.9+ installed. As of now, the project is only compatible with versions between python 3.9 and 3.10.11.
## Running Locally

Recommended: install [Nix](https://nixos.org/download) and [direnv](https://direnv.net) and run:
```sh
make
direnv allow
./manage.py migrate
nix run
```
If not using direnv:
```sh
nix develop # and run `./manage.py migrate` inside
nix run
```

If you do not want to use Nix:
(Note: only tested on Unix-like platforms)

```
make
poetry run python ./manage.py migrate
poetry run python ./manage.py runserver
```
