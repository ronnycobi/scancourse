#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL is up."

echo "Running migrations..."
python manage.py migrate --settings=scancourse.settings.production

echo "Creating superuser if needed..."
python manage.py shell --settings=scancourse.settings.production -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='info@scancourse.co.za').exists():
    User.objects.create_superuser(email='info@scancourse.co.za', username='admin', password='changeme123')
    print('Superuser created.')
"

exec "$@"
