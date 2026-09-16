import os

# Required before any app imports that load Settings.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-32bytes!!")
os.environ.setdefault("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://bfintel:bfintel@localhost:5432/bfintel_test")
os.environ.setdefault("BF_RATE_LIMIT_ENABLED", "true")
os.environ.setdefault("BF_LOGIN_RATE_LIMIT", "5")
os.environ.setdefault("BF_LOGIN_RATE_WINDOW_SECONDS", "60")
