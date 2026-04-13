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
            "https://www.ryanair.com/api/farfnd/v4/oneWayFares"
            "/" + origin + "/" + destination + "/cheapestPerDay"
            "?outboundMonthOfDate=" + month + "&currency=EUR"
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
            print("Ryanair chyba: " + str(e))
    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            results.append((d.strftime("%d.%m"), fares[key]))
    return results

def get_kiwi_prices(origin, destination, days=14):
    results = []
    today = datetime.today()
    date_from = today.strftime("%d/%m/%Y")
    date_to = (today + timedelta(days=days)).strftime("%d/%m/%Y")
    url = "https://api.tequila.kiwi.com/v2/search"
    headers = {
        "apikey": "public",
        "Accept": "application/json"
    }
    params = {
        "fly_from": origin,
        "fly_to": destination,
        "date_from": date_from,
        "date_to": date_to,
        "adults": 1,
        "limit": 50,
        "curr": "EUR",
        "one_for_city": 1,
        "sort": "price"
    }
    fares = {}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        data = r.json()
        for flight in data.get("data", []):
            dep_time = flight.get("dTime")
            price = flight.get("price")
            airline = flight.get("airlines", ["?"])[0]
            if dep_time and price:
                d = datetime.fromtimestamp(dep_time)
                key = d.strftime("%Y-%m-%d")
                label = d.strftime("%d.%m")
                if key not in fares or price < fares[key][0]:
                    fares[key] = (price, airline)
    except Exception as e:
        print("Kiwi chyba: " + str(e))

    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            price, airline = fares[key]
            results.append((d.strftime("%d.%m"), price, airline))
    return results

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def format_section(title, flights, use_airline=False):
    msg = title + "\n"
    if flights:
        for item in flights:
            if use_airline:
                date, price, airline = item
            else:
                date, price = item
                airline = ""
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            line = emoji + " " + date + " — <b>" + str(int(price)) + " €</b>"
            if use_airline:
                line += " (" + airline + ")"
            msg += line + "\n"
    else:
        msg += "Žiadne lety nenájdené\n"
    return msg

def main():
    bts_tps = get_ryanair_prices("BTS", "TPS")
    tps_bts = get_ryanair_prices("TPS", "BTS")
    bts_pmo = get_kiwi_prices("BTS", "PMO")
    pmo_bts = get_kiwi_prices("PMO", "BTS")

    msg = "✈️ <b>LETENKY — najbližších 14 dní</b>\n\n"
    msg += format_section("🛫 <b>Bratislava → Trapani (Ryanair)</b>", bts_tps)
    msg += "\n"
    msg += format_section("🔄 <b>Trapani → Bratislava (Ryanair)</b>", tps_bts)
    msg += "\n"
    msg += format_section("🛫 <b>Bratislava → Palermo (všetky aerolinky)</b>", bts_pmo, use_airline=True)
    msg += "\n"
    msg += format_section("🔄 <b>Palermo → Bratislava (všetky aerolinky)</b>", pmo_bts, use_airline=True)
    msg += "\n🟢 do 30€  🟡 do 60€  🔴 60€+"

    send_telegram(msg)
    print("Odoslane!")

if __name__ == "__main__":
    main()
