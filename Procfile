web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
release: python -c "from app.db.database import init_db; from app.db.seed import seed_all; init_db(); seed_all()"
