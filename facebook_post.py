import requests
from datetime import datetime, timedelta
import os

FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
KIWI_LINK = "https://kiwi.tpx.gr/41mqIeVX"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ryanair.com/",
    "Origin": "https://www.ryanair.com"
}

DESTINATIONS = {
    "TPS": "Trapani 🇮🇹",
    "PMO": "Palermo 🇮🇹",
    "NAP": "Neapol 🇮🇹",
    "CIA": "Rím 🇮🇹",
    "BGY": "Miláno 🇮🇹",
    "BRI": "Bari 🇮🇹",
    "PSA": "Pisa 🇮🇹",
    "LME": "Lamezia Terme 🇮🇹",
    "BCN": "Barcelona 🇪🇸",
    "ALC": "Alicante 🇪🇸",
    "AGP": "Malaga 🇪🇸",
    "ACE": "Lanzarote 🇪🇸",
    "STN": "Londýn 🇬🇧",
    "MAN": "Manchester 🇬🇧",
    "EDI": "Edinburgh 🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "DUB": "Dublin 🇮🇪",
    "ATH": "Atény 🇬🇷",
    "SKG": "Thessaloniki 🇬🇷",
    "MLA": "Malta 🇲🇹",
    "EIN": "Eindhoven 🇳🇱",
    "CRL": "Brusel 🇧🇪",
    "DLM": "Dalaman 🇹🇷",
    "TSF": "Benátky 🇮🇹",
    "PRG": "Praha 🇨🇿",
    "WAW": "Varšava 🇵🇱"
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
            print("Chyba " + destination + ": " + str(e))
    for i in range(days):
        d = today + timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        if key in fares:
            results.append((d.strftime("%d.%m"), fares[key], destination))
    return results

def post_to_facebook(message):
    url = "https://graph.facebook.com/v19.0/" + FB_PAGE_ID + "/feed"
    data = {
        "message": message,
        "access_token": FB_PAGE_TOKEN
    }
    r = requests.post(url, data=data)
    print("Facebook: " + r.text)

def main():
    all_flights = []
    for iata, name in DESTINATIONS.items():
        flights = get_ryanair_prices("BTS", iata)
        for date, price, dest in flights:
            all_flights.append((date, price, name))

    all_flights.sort(key=lambda x: x[1])

    top10 = []
    seen_dates = {}
    for date, price, dest in all_flights:
        if dest not in seen_dates:
            seen_dates[dest] = True
            top10.append((date, price, dest))
        if len(top10) >= 10:
            break

    if not top10:
        top10 = all_flights[:10]

    today_str = datetime.today().strftime("%d.%m.%Y")

    msg = "✈️ TOP 10 NAJLACNEJŠÍCH LETENIEK Z BRATISLAVY\n"
    msg += "📅 " + today_str + " | Najbližších 14 dní\n\n"

    for i, (date, price, dest) in enumerate(top10, 1):
        emoji = "🟢" if price < 20 else "🟡" if price < 40 else "🔴"
        msg += str(i) + ". " + emoji + " " + date + " → " + dest + " — " + str(int(price)) + " €\n"

    msg += "\n👉 Rezervuj tu: " + KIWI_LINK
    msg += "\n\n#letenky #cestovanie #výlety #lacnéletenky #Bratislava #reklama"

    post_to_facebook(msg)
    print("Hotovo!")

if __name__ == "__main__":
    main()
