***This project is no longer being developed.***

# lifescheme
Lifescheme is a productivity web application created in Django that allows its users to manage their time
by scheduling tasks using time-blocking technique.


# Running locally
To run the web app locally on your computer run the following commands.

## Windows

```
git clone https://github.com/iangitonga/lifescheme.git
cd lifescheme/
python -m venv venv/
venv\bin\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Linux and Mac
```
git clone https://github.com/iangitonga/lifescheme.git
cd lifescheme/
python3 -m venv venv/
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

You can then access the site at http://127.0.0.1:8000/
