# Goblin Scout

A lightweight Python script that watches your **Steam wishlist** and alerts you on **Telegram** when a game hits a **historical low** price (via [IsThereAnyDeal](https://isthereanydeal.com)).

Built to stay small: no database, no framework, just scripts, a JSON cache, and `requests`.

## What it does

1. Fetches your Steam wishlist (AppIDs)
2. Maps each AppID to an ITAD (IsThereAnyDeal) game ID (cached in `game_id_mapping.json`, including title and cover image)
3. Loads a price overview for Brazil (`country=BR`) from selected shops only:
   - GamersGate, GreenManGaming, Nuuvem, Steam
4. Flags deals where the **current best price among those shops** is at or within **5%** of the **global historical low** (`NEAR_LOW_MARGIN` in `config.py`)
5. Sends a Telegram message using `templates/alert_deal.html`
6. Avoids spam: stores `last_alert` (price + shop) and clears it when the price changes, so the same historical low can notify again after the sale ends

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install requests