from datetime import datetime

from config import get_env, load_env
from providers import ITADProvider, SteamProvider
from scout import run


def main():
    started = datetime.now()
    print(f"=== started {started:%Y-%m-%d %H:%M:%S} ===", flush=True)
    try:
        load_env()
        steam = SteamProvider(get_env("STEAM_ID"))
        itad = ITADProvider(get_env("ITAD_API_KEY"))
        run(steam, itad)
    finally:
        ended = datetime.now()
        elapsed = (ended - started).total_seconds()
        print(
            f"=== finished {ended:%Y-%m-%d %H:%M:%S} (elapsed {elapsed:.0f}s) ===",
            flush=True,
        )


if __name__ == "__main__":
    main()
