FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Served as ASGI, not `flask run`: a WSGI server gives every request its own
# event loop, which AsyncMongoClient refuses to work across. See app/wsgi.py.
CMD ["hypercorn", "app.wsgi:asgi_app", "--bind", "0.0.0.0:5000"]
