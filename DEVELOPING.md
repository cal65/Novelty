# Instructions on how to develop Novelty

## Local setup

1. Install `uv` for package management following the [instructions](https://docs.astral.sh/uv/getting-started/installation/)
2. Run `uv sync` to install dependencies. 
   * This will make a virtual environment at `.venv`, which you can activate by running `. .venv/bin/activate` in your shell
3. Run `uv run manage.py tailwind start` to start a server that will recompile the tailwind CSS as needed
4. Run `uv run manage.py runserver` to start the Django server

Not included in these instructions: setting up the database. It would be easiest to restore the database from a backup,
but you can also run `uv run manage.py migrate` to create the database and tables from scratch.


## Deploying to production

1. Make sure the latest version of the tailwind CSS has been built locally and checked into git: `uv run manage.py tailwind build`
2. ssh to the production webserver and pull from git
3. Kill gunicorn if it's already running: `pkill gunicorn`
4. Run `./scripts/run_production.sh` to start the server