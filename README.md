create venv
install requirements.txt
run migrations
createsuperuser
python manage.py seed
python manage.py runserver

python manage.py process_tasks  ( to run bg task )
