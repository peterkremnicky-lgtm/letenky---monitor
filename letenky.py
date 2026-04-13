import requests
from datetime import datetime, timedelta
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HEADERS_RYANAIR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ryanair.com/",
    "Origin": "https://www.ryanair.com"
}

HEADERS_WIZZAIR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://wizzair.com/",
    "Origin": "https://wizzair.com"
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
            "https://www.ryanair.com/api/farfnd/v4/oneWayFares"
            "/" + origin + "/" + destination + "/cheapestPerDay"
            "?outboundMonthOfDate=" + month + "&currency=EUR"
        )
        try:
            r = requests.get(url, headers=HEADERS_RYANAIR, timeout=15)
            data = r.json()
            for item in data.get("outbound", {}).get("fares", []):
                date = item.get("day")
                price_obj = item.get("price")
                if date and price_obj and price_obj.get("value") is not None:
                    fares[date] = price_obj["value"]
        except Exception as e:
            print("Ryanair chyba: " + str(e))
    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            results.append((d.strftime("%d.%m"), fares[key]))
    return results

def get_wizzair_prices(origin, destination, days=14):
    results = []
    today = datetime.today()
    fares = {}
    for i in range(days):
        d = today + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        url = "https://be.wizzair.com/24.4.0/Api/search/search"
        payload = {
            "isFlightChange": False,
            "isSeniorOrStudent": False,
            "flightList": [
                {
                    "departureStation": origin,
                    "arrivalStation": destination,
                    "date": date_str
                }
            ],
            "adultCount": 1,
            "childCount": 0,
            "infantCount": 0,
            "wdc": False
        }
        try:
            r = requests.post(url, json=payload, headers=HEADERS_WIZZAIR, timeout=15)
            data = r.json()
            flights = data.get("outboundFlights", [])
            if flights:
                prices = [f.get("price", {}).get("amount") for f in flights if f.get("price")]
                if prices:
                    fares[date_str] = min(p for p in prices if p)
        except Exception as e:
            print("Wizz Air chyba: " + str(e))
    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            results.append((d.strftime("%d.%m"), fares[key]))
    return results

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def main():
    bts_tps = get_ryanair_prices("BTS", "TPS")
    tps_bts = get_ryanair_prices("TPS", "BTS")
    bts_pmo_ry = get_ryanair_prices("BTS", "PMO")
    pmo_bts_ry = get_ryanair_prices("PMO", "BTS")
    bts_pmo_wz = get_wizzair_prices("BTS", "PMO")
    pmo_bts_wz = get_wizzair_prices("PMO", "BTS")

    msg = "✈️ <b>LETENKY — najbližších 14 dní</b>\n\n"

    msg += "🛫 <b>Bratislava → Trapani (Ryanair)</b>\n"
    if bts_tps:
        for date, price in bts_tps:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🔄 <b>Trapani → Bratislava (Ryanair)</b>\n"
    if tps_bts:
        for date, price in tps_bts:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n✈️ <b>Bratislava → Palermo (Ryanair)</b>\n"
    if bts_pmo_ry:
        for date, price in bts_pmo_ry:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🔄 <b>Palermo → Bratislava (Ryanair)</b>\n"
    if pmo_bts_ry:
        for date, price in pmo_bts_ry:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n✈️ <b>Bratislava → Palermo (Wizz Air)</b>\n"
    if bts_pmo_wz:
        for date, price in bts_pmo_wz:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🔄 <b>Palermo → Bratislava (Wizz Air)</b>\n"
    if pmo_bts_wz:
        for date, price in pmo_bts_wz:
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"

    msg += "\n🟢 do 30€  🟡 do 60€  🔴 60€+"

    send_telegram(msg)
    print("Odoslane!")

if __name__ == "__main__":
    main()
