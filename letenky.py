import requests
from datetime import datetime, timedelta
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ryanair.com/",
    "Origin": "https://www.ryanair.com"
}

def get_ryanair_prices(origin, destination, days=14):
    results = []
    today = datetime.today()

    months = set()
    for i in range(days):
        d = today + timedelta(days=i)
        months.add(d.strftime("%Y-%m-01"))

    fares = {}
    for month in months:
        url = (
            f"https://www.ryanair.com/api/farfnd/v4/oneWayFares"
            f"/{origin}/{destination}/cheapestPerDay"
            f"?outboundMonthOfDate={month}&currency=EUR"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            data = r.json()
            for item in data.get("outbound", {}).get("fares", []):
                date = item.get("day")
                price_obj = item.get("price")
                if date and price_obj and price_obj.get("value") is not None:
                    fares[date] = price_obj["value"]
        except Exception as e:
            print(f"Chyba {origin}->{destination}: {e}")

    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            results.append((d.strftime("%d.%m"), fares[key]))

    return results

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def main():
    bts_tps = get_ryanair_prices("BTS", "TPS")
    tps_bts = get_ryanair_prices("TPS", "BTS")
    bts_pmo = get_ryanair_prices("BTS", "PMO")
    pmo_bts = get_ryanair_prices("PMO", "BTS")

    msg = "✈️ <b>LETENKY — najbližších 14 dní</b>\n\n"

    msg += "🛫 <b>Bratislava → Trapani</b>\n"
    if bts_tps:
        for date, price in bts_tps:
            emoji = "🟢" if price < 30 else "🟡" if price < 60 else "🔴"
            msg += f"{emoji} {date} — <b>{price:.0f} €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🔄 <b>Trapani → Bratislava</b>\n"
    if tps_bts:
        for date, price in tps_bts:
            emoji = "🟢" if price < 30 else "🟡" if price < 60 else "🔴"
            msg += f"{emoji} {date} — <b>{price:.0f} €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n✈️ <b>Bratislava → Palermo</b>\n"
    if bts_pmo:
        for date, price in bts_pmo:
            emoji = "🟢" if price < 30 else "🟡" if price < 60 else "🔴"
            msg += f"{emoji} {date} — <b>{price:.0f} €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🔄 <b>Palermo → Bratislava</b>\n"
    if pmo_bts:
        for date, price in pmo_bts:
            emoji = "🟢" if price < 30 else "🟡" if price < 60 else "🔴"
            msg += f"{emoji} {date} — <b>{price:.0f} €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🟢 do 30€  🟡 do 60€  🔴 60€+"

    send_telegram(msg)
    print("Odoslané!")

if __name__ == "__main__":
    main()
