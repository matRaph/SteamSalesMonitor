import json
from pathlib import Path
from datetime import datetime

class GameIdMapping:
    def __init__(self, path="game_id_mapping.json"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {}

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def get(self, appid):
        return self.data.get(str(appid))

    def set(self, appid, itad_id, title=None, image=None):
        key = str(appid)
        entry = self.data.get(key, {})
        if isinstance(entry, str):
            entry = {"id": entry}
        entry["id"] = itad_id
        if title is not None:
            entry["title"] = title
        if image is not None:
            entry["image"] = image
        self.data[key] = entry

    def needs_enrichment(self, appid):
        entry = self.get(appid)
        if entry is None:
            return True
        if isinstance(entry, str):
            return True
        return not entry.get("title") or not entry.get("image")

    def itad_ids(self):
        ids = []
        for value in self.data.values():
            ids.append(value["id"] if isinstance(value, dict) else value)
        return ids

    def entry_for_itad_id(self, itad_id):
        for appid, value in self.data.items():
            gid = value["id"] if isinstance(value, dict) else value
            if gid == itad_id:
                if isinstance(value, dict):
                    return {"appid": int(appid), **value}
                return {
                    "appid": int(appid),
                    "id": value,
                    "title": "Unknown",
                    "image": None,
                }
        return None

    def title_for(self, itad_id):
        entry = self.entry_for_itad_id(itad_id)
        if not entry:
            return "Unknown"
        return entry.get("title") or "Unknown"

    def image_for(self, itad_id):
        entry = self.entry_for_itad_id(itad_id)
        if not entry:
            return None
        return entry.get("image")

    def appid_for(self, itad_id):
        entry = self.entry_for_itad_id(itad_id)
        return entry["appid"] if entry else None

    def _entry_ref(self, itad_id):
        for appid, value in self.data.items():
            gid = value["id"] if isinstance(value, dict) else value
            if gid != itad_id:
                continue
            if isinstance(value, str):
                value = {"id": value}
                self.data[appid] = value
            return appid, value
        return None, None

    def should_alert(self, itad_id, price_int):
        _, entry = self._entry_ref(itad_id)
        if not entry:
            return True
        last = entry.get("last_alert")
        if not last or not isinstance(last, dict):
            return True
        return last.get("price_int") != price_int

    def mark_alerted(self, itad_id, price_int, shop_id):
        _, entry = self._entry_ref(itad_id)
        if not entry:
            return
        entry["last_alert"] = {
            "price_int": price_int,
            "shop_id": shop_id,
            "sent_at": datetime.now().isoformat(),
        }
        self.save()

    def clear_stale_alerts(self, overview):
        dirty = False
        seen_ids = set()

        for item in overview.get("prices", []):
            seen_ids.add(item["id"])
            current = item.get("current")
            if not current:
                continue
            _, entry = self._entry_ref(item["id"])
            if not entry:
                continue
            last = entry.get("last_alert")
            if not last:
                continue
            if not isinstance(last, dict):
                entry.pop("last_alert", None)
                dirty = True
                continue
            current_price = current["price"]["amountInt"]
            if last.get("price_int") != current_price:
                entry.pop("last_alert", None)
                dirty = True
                print(
                    f"Cleared stale alert for {entry.get('title', item['id'])} "
                    f"(was {last.get('price_int')}, now {current_price})"
                )

        for appid, value in list(self.data.items()):
            if not isinstance(value, dict) or not value.get("last_alert"):
                continue
            if value.get("id") in seen_ids:
                continue
            title = value.get("title", appid)
            value.pop("last_alert", None)
            dirty = True
            print(f"Cleared stale alert for {title} (no longer in overview)")

        if dirty:
            self.save()
