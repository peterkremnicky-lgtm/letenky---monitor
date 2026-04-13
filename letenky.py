import requests
from datetime import datetime, timedelta
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

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
            f"https://services-api.ryanair.com/farfnd/3/oneWayFares"
            f"/{origin}/{destination}/cheapestPerDay"
            f"?outboundMonthOfDate={month}"
        )
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            for item in data.get("outbound", {}).get("fares", []):
                date = item.get("day")
                price = item.get("price", {}).get("value")
                if date and price is not None:
                    fares[date] = price
        except Exception as e:
            print(f"Chyba: {e}")
    
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
    
    msg += "\n🟢 do 30€  🟡 do 60€  🔴 60€+"

if __name__ == "__main__":
    main()
