import time
from pathlib import Path

from config import NEAR_LOW_MARGIN, get_env
from mapping import GameIdMapping
from providers import TelegramProvider

template = Path("templates/alert_deal.html").read_text(encoding="utf-8")


def wishlist_appids(steam):
    data = steam.get_my_wishlist()
    return [item["appid"] for item in data["response"]["items"]]


def game_image_url(game):
    assets = game.get("assets") or {}
    return (
        assets.get("banner600")
        or assets.get("banner400")
        or assets.get("banner300")
        or None
    )


def sync_mapping(itad, mapping, appids):
    removed = mapping.prune_not_in_wishlist(appids)
    for appid, title in removed:
        print(f"Removed {title} (appid {appid}) — no longer on wishlist")

    for appid in appids:
        if not mapping.needs_enrichment(appid):
            continue

        print(f"Looking up ITAD ID for Steam appid {appid}")
        data = itad.lookup_game(appid)
        if data.get("found") and data.get("game"):
            game = data["game"]
            title = game.get("title", "Unknown")
            image = game_image_url(game)
            mapping.set(appid, game["id"], title=title, image=image)
            print(f"Mapped appid {appid} -> {game['id']} ({title})")
        else:
            print(f"No ITAD match found for appid {appid}")
    mapping.save()


def refresh_stale_ids(itad, mapping, missing_ids):
    updated = False
    no_price = []
    for bad_id in missing_ids:
        appid = mapping.appid_for(bad_id)
        data = itad.lookup_game(appid)
        game = data.get("game") if data.get("found") else None
        title = game.get("title", "Unknown") if game else "Unknown"
        image = game_image_url(game) if game else None
        new_id = game.get("id") if game else None

        print(f"Checking appid {appid} ({title}) — missing from overview: {bad_id}")

        if new_id and new_id != bad_id:
            mapping.set(appid, new_id, title=title, image=image)
            updated = True
            print(f"Updated appid {appid} ({title}): {bad_id} -> {new_id}")
        else:
            if game:
                mapping.set(appid, bad_id, title=title, image=image)
            no_price.append((appid, title))
            print(f"No price for appid {appid} ({title}) — id still valid")

    mapping.save()
    return updated, no_price


def get_alerts(overview):
    alerts = []
    for item in overview.get("prices", []):
        current = item.get("current")
        lowest = item.get("lowest")
        if not current or not lowest:
            continue
        current_price = current["price"]["amountInt"]
        lowest_price = lowest["price"]["amountInt"]
        if (
            current_price <= lowest_price * (1 + NEAR_LOW_MARGIN)
            and current_price < current["regular"]["amountInt"]
        ):
            alerts.append(item)
    return alerts


def send_alerts(alerts, mapping):
    telegram = TelegramProvider(
        get_env("TELEGRAM_API_TOKEN"), get_env("TELEGRAM_CHAT_ID")
    )

    if not alerts:
        print("No alerts to send")
        return

    print(f"Sending {len(alerts)} alerts")
    for alert in alerts:
        title = mapping.title_for(alert["id"])
        image = mapping.image_for(alert["id"])
        price = alert["current"]["price"]
        shop = alert["current"]["shop"]

        if not mapping.should_alert(alert["id"], price["amountInt"]):
            print(f"Skipping {title} — already alerted at this price")
            continue

        response = telegram.send_message(
            photo=image,
            html=template.format(
                game_title=title,
                current_price="{:.2f}".format(float(price["amount"])).replace(".", ","),
                store_name=shop["name"],
                offer_url=alert["current"]["url"],
            ),
        )
        if not response["ok"]:
            print(f"Failed to send alert: {response['description']}")
            return
        print(f"Alert sent: {response['result']['message_id']} ({title})")
        mapping.mark_alerted(alert["id"], price["amountInt"], shop["id"])
        # TODO: see if theres a better way to avoid telegram rate limiting (maybe check for batch sending?)
        time.sleep(2)


def run(steam, itad):
    appids = wishlist_appids(steam)
    print(f"Loaded wishlist with {len(appids)} games")

    mapping = GameIdMapping()
    print(f"Loaded mapping with {len(mapping.data)} cached entries")

    sync_mapping(itad, mapping, appids)

    print(f"Fetching price overview for {len(mapping.itad_ids())} games")
    overview = itad.get_game_prices_overview(mapping.itad_ids())

    mapping.clear_stale_alerts(overview)

    alerts = get_alerts(overview)
    send_alerts(alerts, mapping)

    returned = {item["id"] for item in overview.get("prices", [])}
    missing = set(mapping.itad_ids()) - returned

    if missing:
        print(f"Found {len(missing)} IDs missing from overview")
        updated, no_price = refresh_stale_ids(itad, mapping, missing)
        if updated:
            print("Re-fetching price overview after mapping refresh")
            overview = itad.get_game_prices_overview(mapping.itad_ids())
        if no_price:
            print("Games without prices:")
            for appid, title in no_price:
                print(f"  - {title} (appid {appid})")
    else:
        print("All ITAD IDs present in overview")

    return overview
