from config import get_env, load_env
from providers import ITADProvider, SteamProvider
from scout import run

def main():
    load_env()
    steam = SteamProvider(get_env("STEAM_ID"))
    itad = ITADProvider(get_env("ITAD_API_KEY"))
    run(steam, itad)

if __name__ == "__main__":
    main()