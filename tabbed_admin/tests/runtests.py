import sys

import django
from django.conf import settings
from django.test.runner import DiscoverRunner


def main() -> None:
    settings.configure(
        SECRET_KEY="tabbed-admin-tests-only",
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        ROOT_URLCONF="tabbed_admin.tests.urls",
        STATIC_URL="/static/",
        TABBED_ADMIN_USE_JQUERY_UI=True,
        ALLOWED_HOSTS=["testserver"],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ]
                },
            }
        ],
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.admin",
            "tabbed_admin",
            "tabbed_admin.tests",
        ],
    )
    django.setup()
    sys.exit(DiscoverRunner(verbosity=2).run_tests(["tabbed_admin.tests"]))


if __name__ == "__main__":
    main()
