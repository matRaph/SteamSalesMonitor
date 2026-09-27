import os


def load_env(path=".env"):
    with open(path) as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            key, value = line.split("=", 1)
            os.environ[key] = value


def get_env(name):
    value = os.environ.get(name)

    if value is None:
        raise RuntimeError(
            "Environment variable '{}' is not configured".format(name)
        )

    return value