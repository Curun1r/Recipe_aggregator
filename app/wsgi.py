from asgiref.wsgi import WsgiToAsgi

from app import create_app

# Why this file exists:
# Flask is WSGI, so `flask run` calls each async view through
# asgiref's async_to_sync, which spins up a NEW event loop per request.
# AsyncMongoClient binds to the loop it was created on and raises
# "Cannot use AsyncMongoClient in different event loop" on the next one.
#
# Served as ASGI, asgiref keeps one loop (the server's) and runs the
# views' coroutines on it, so the client stays on a single loop.
# Run with: hypercorn app.wsgi:asgi_app --bind 0.0.0.0:5000
asgi_app = WsgiToAsgi(create_app())
