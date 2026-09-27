import json
from pathlib import Path


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
