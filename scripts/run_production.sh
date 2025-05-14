#!/bin/bash

set -e

# Copy static assets from each app into the top-level static directory
uv run -- manage.py collectstatic --no-input

nohup uv run -- gunicorn goodreads_history.wsgi >> /var/log/gunicorn/logs.txt &