import requests
from datetime import datetime, timedelta
import os
import random

FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_GROUP_ID = os.environ.get("FB_GROUP_ID")
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
KIWI_LINK = "https://kiwi.tpx.gr/41mqIeVX"
FB_PAGE_NAME = "Kedykam"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.ryanair.com/",
    "Origin": "https://www.ryanair.com"
}

MOTIVACIE = [
    "😴 Unavený z práce? Možno je čas na malý útek... Pozri čo sme našli pre teba!",
    "☀️ Slnko, more, pohoda... a letenka za pár eur. Čo viac potrebuješ?",
    "🌍 Život je krátky. Cestuj viac, ľutuj menej!",
    "💼 Pondelok ťa dobíja? Naplánuj si niečo na čo sa tešiť!",
    "🏖️ Predstav si: teplý piesok, modré more, žiadne starosti...",
    "🎒 Najlepšia investícia? Zážitky, nie veci. Tu sú dnešné ponuky!",
    "✈️ Niekedy stačí jeden impulz a dovolenka je naplánovaná!",
    "🌅 Nový výhľad mení perspektívu. Kedy si naposledy cestoval?",
    "🍕 Pravá talianska pizza, španielske tapas alebo írske pivo? Vyber si!",
    "💆 Relax nie je luxus — je to nevyhnutnosť. A my ti ho pomôžeme zorganizovať!",
    "🗺️ Každá cesta začína jedným krokom... alebo jedným kliknutím!",
    "🌞 Pretože šedý pondelok vyzerá lepšie s výhľadom na cestu vpred!",
    "🎉 Najlacnejšie letenky dnes ráno — vyber si destináciu snov!",
    "🧳 Balíček je vždy pripravený. Čaká len na lístok!",
    "💛 Investuj do spomienok — vráti sa ti to s úrokmi!"
]

DESTINATIONS = {
    "TPS": ("Trapani 🇮🇹", "Trapani Sicily beach"),
    "PMO": ("Palermo 🇮🇹", "Palermo Sicily"),
    "NAP": ("Neapol 🇮🇹", "Naples Italy Vesuvius"),
    "CIA": ("Rím 🇮🇹", "Rome Colosseum"),
    "BGY": ("Miláno 🇮🇹", "Milan Italy cathedral"),
    "BRI": ("Bari 🇮🇹", "Bari Italy old town"),
    "PSA": ("Pisa 🇮🇹", "Pisa leaning tower"),
    "LME": ("Lamezia Terme 🇮🇹", "Calabria Italy beach"),
    "BCN": ("Barcelona 🇪🇸", "Barcelona Sagrada Familia"),
    "ALC": ("Alicante 🇪🇸", "Alicante Spain beach"),
    "AGP": ("Malaga 🇪🇸", "Malaga Spain beach"),
    "ACE": ("Lanzarote 🇪🇸", "Lanzarote volcanic beach"),
    "STN": ("Londýn 🇬🇧", "London Big Ben"),
    "MAN": ("Manchester 🇬🇧", "Manchester England"),
    "EDI": ("Edinburgh 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Edinburgh castle Scotland"),
    "DUB": ("Dublin 🇮🇪", "Dublin Ireland"),
    "ATH": ("Atény 🇬🇷", "Athens Acropolis"),
    "SKG": ("Thessaloniki 🇬🇷", "Thessaloniki Greece"),
    "MLA": ("Malta 🇲🇹", "Malta sea blue"),
    "EIN": ("Eindhoven 🇳🇱", "Eindhoven Netherlands"),
    "CRL": ("Brusel 🇧🇪", "Brussels Belgium"),
    "DLM": ("Dalaman 🇹🇷", "Dalaman Turkey beach"),
    "TSF": ("Benátky 🇮🇹", "Venice Italy canals"),
    "PRG": ("Praha 🇨🇿", "Prague castle"),
    "WAW": ("Varšava 🇵🇱", "Warsaw Poland")
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

def get_unsplash_photo(query):
    try:
        url = "https://api.unsplash.com/photos/random"
        params = {
            "query": query,
            "orientation": "landscape",
            "client_id": UNSPLASH_KEY
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data.get("urls", {}).get("regular")
    except Exception as e:
        print("Unsplash chyba: " + str(e))
        return None

def post_to_facebook_with_photo(target_id, message, photo_url, token):
    try:
        if photo_url:
            url = "https://graph.facebook.com/v19.0/" + target_id + "/photos"
            data = {
                "url": photo_url,
                "caption": message,
                "access_token": token
            }
        else:
            url = "https://graph.facebook.com/v19.0/" + target_id + "/feed"
            data = {
                "message": message,
                "access_token": token
            }
        r = requests.post(url, data=data)
        result = r.json()
        print("Facebook " + target_id + ": " + str(result))
        return result.get("id") or result.get("post_id")
    except Exception as e:
        print("Facebook chyba: " + str(e))
        return None

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def main():
    all_flights = []
    for iata, (name, _) in DESTINATIONS.items():
        flights = get_ryanair_prices("BTS", iata)
        for date, price, dest in flights:
            all_flights.append((date, price, name, iata))

    all_flights.sort(key=lambda x: x[1])

    top10 = []
    seen_dest = {}
    for date, price, name, iata in all_flights:
        if name not in seen_dest:
            seen_dest[name] = True
            top10.append((date, price, name, iata))
        if len(top10) >= 10:
            break

    if not top10:
        top10 = all_flights[:10]

    cheapest_iata = top10[0][3] if top10 else "TPS"
    photo_query = DESTINATIONS.get(cheapest_iata, ("", "travel beach"))[1]
    photo_url = get_unsplash_photo(photo_query)

    today_str = datetime.today().strftime("%d.%m.%Y")
    motivacia = random.choice(MOTIVACIE)

    msg = motivacia + "\n\n"
    msg += "✈️ TOP 10 NAJLACNEJŠÍCH LETENIEK Z BRATISLAVY\n"
    msg += "📅 " + today_str + " | Najbližších 14 dní\n\n"

    for i, (date, price, name, iata) in enumerate(top10, 1):
        emoji = "🟢" if price < 20 else "🟡" if price < 40 else "🔴"
        msg += str(i) + ". " + emoji + " " + date + " → " + name + " — " + str(int(price)) + " €\n"

    msg += "\n👉 Rezervuj tu: " + KIWI_LINK
    msg += "\n\n#letenky #cestovanie #výlety #lacnéletenky #Bratislava #reklama"

    post_id = post_to_facebook_with_photo(FB_PAGE_ID, msg, photo_url, FB_PAGE_TOKEN)

    fb_post_link = "https://www.facebook.com/" + FB_PAGE_ID
    if post_id:
        fb_post_link = "https://www.facebook.com/" + str(post_id).replace("_", "/posts/")

    telegram_notif = "✅ <b>Post zverejnený na Kedykam!</b>\n\n"
    telegram_notif += "📱 Zdieľaj do skupiny ako stránka Kedykam:\n"
    telegram_notif += "👉 " + fb_post_link + "\n\n"
    telegram_notif += "⏱️ Trvá to 10 sekúnd!"

    send_telegram(telegram_notif)
    print("Hotovo!")

if __name__ == "__main__":
    main()
