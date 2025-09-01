web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn stockchart_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60 --keep-alive 2
