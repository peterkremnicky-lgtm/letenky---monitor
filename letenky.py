import requests
from datetime import datetime, timedelta
import os
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

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

def get_apify_prices(origin, destination, days=14):
    results = []
    today = datetime.today()
    date_from = today.strftime("%Y-%m-%d")
    date_to = (today + timedelta(days=days)).strftime("%Y-%m-%d")

    run_url = "https://api.apify.com/v2/acts/rigelblu~google-flights-scraper/runs"
    payload = {
        "origin": origin,
        "destination": destination,
        "departureDate": date_from,
        "returnDate": date_to,
        "currency": "EUR",
        "adults": 1
    }
    headers = {"Content-Type": "application/json"}
    params = {"token": APIFY_TOKEN}

    try:
        r = requests.post(run_url, json=payload, headers=headers, params=params, timeout=30)
        run_data = r.json()
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            print("Apify run sa nespustil")
            return results

        # Čakáme kým dobehne (max 60 sekúnd)
        for _ in range(12):
            time.sleep(5)
            status_url = "https://api.apify.com/v2/acts/rigelblu~google-flights-scraper/runs/" + run_id
            sr = requests.get(status_url, params=params, timeout=15)
            status = sr.json().get("data", {}).get("status")
            if status == "SUCCEEDED":
                break

        dataset_url = "https://api.apify.com/v2/acts/rigelblu~google-flights-scraper/runs/" + run_id + "/dataset/items"
        dr = requests.get(dataset_url, params=params, timeout=15)
        for flight in dr.json():
            date = flight.get("date")
            price = flight.get("price")
            if date and price:
                results.append((date, price))
    except Exception as e:
        print("Apify chyba: " + str(e))

    return results

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def format_section(title, flights):
    msg = title + "\n"
    if flights:
        for item in flights:
            date, price = item[0], item[1]
            if price < 30:
                emoji = "🟢"
            elif price < 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            msg += emoji + " " + date + " — <b>" + str(int(price)) + " €</b>\n"
    else:
        msg += "Žiadne lety nenájdené\n"
    return msg

def main():
    bts_tps = get_ryanair_prices("BTS", "TPS")
    tps_bts = get_ryanair_prices("TPS", "BTS")
    bts_pmo = get_ryanair_prices("BTS", "PMO")
    pmo_bts = get_ryanair_prices("PMO", "BTS")

    msg = "✈️ <b>LETENKY — najbližších 14 dní</b>\n\n"
    msg += format_section("🛫 <b>Bratislava → Trapani (Ryanair)</b>", bts_tps)
    msg += "\n"
    msg += format_section("🔄 <b>Trapani → Bratislava (Ryanair)</b>", tps_bts)
    msg += "\n"
    msg += format_section("🛫 <b>Bratislava → Palermo (Ryanair)</b>", bts_pmo)
    msg += "\n"
    msg += format_section("🔄 <b>Palermo → Bratislava (Ryanair)</b>", pmo_bts)
    msg += "\n🟢 do 30€  🟡 do 60€  🔴 60€+"

    send_telegram(msg)
    print("Odoslane!")

if __name__ == "__main__":
    main()
