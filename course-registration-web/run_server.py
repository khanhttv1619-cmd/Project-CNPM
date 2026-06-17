import os
import sys

from app import app


stdout = open("server-runtime.log", "a", encoding="utf-8", buffering=1)
stderr = open("server-runtime.err", "a", encoding="utf-8", buffering=1)
sys.stdout = stdout
sys.stderr = stderr

app.run(
    host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
    port=int(os.getenv("FLASK_RUN_PORT", "5055")),
    debug=False,
    use_reloader=False,
)
