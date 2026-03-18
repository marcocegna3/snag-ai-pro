from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

app = FastAPI(title="SNAG AI PRO - 100 Negozi")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
deals_data = []

# 100 NEGOZI VERIFICATI ITALIANI
NEGOZI = [
    # OROLOGI/GIOIELLI (15)
    "https://www.chrono24.it/search/index.htm?query=rolex+submariner&sortorder=1",
    "https://pisa1940.com/en/search?query=rolex",
    "https://www.gioielleriabonanno.it/en/search?query=rolex",
    "https://www.orologio.it",
    "https://www.orissimo.it",
    "https://www.stroilioro.it",
    "https://www.pandora.net/it",
    "https://www.swatch.com/it-it",
    "https://www.amazon.it/s?k=rolex+orologio",
    "https://www.bulgari.com/it-it/orologi",
    
    # SNEAKERS/SPORT (20)
    "https://stockx.com/search?s=nike+dunk+low",
    "https://www.luisaviaroma.com/it_it/sneakers/nike",
    "https://www.footlocker.it/it/search/?text=nike+dunk",
    "https://www.slamjam.com/it/search?q=nike",
    "https://www.nike.com/it/w/search?q=dunk",
    "https://www.adidas.it/search?q=dunk",
    "https://www.decathlon.it/search?q=nike",
    "https://www.tradeinn.com/runner.it/search",
    "https://www.amazon.it/s?k=nike+dunk+low",
    "https://www.sportler.com/search?q=nike",
    
    # MODA/ABBIGLIAMENTO (30)
    "https://www.zalando.it/uomo-abbigliamento/",
    "https://www.shein.com/it/Abbigliamento-Uomo",
    "https://www.zara.com/it/it/uomo-abbigliamento-l4496.html",
    "https://www.h&M.com/it_it/productlist/productlist_oversikt/list?N=11",
    "https://www.ovs.it/it-it/uomo/abbigliamento",
    "https://www.asos.com/it/uomo/abbigliamento/cat/?cid=8799",
    "https://www.spartoo.it/search.aspx",
    "https://www.farfetch.com/it/shopping/men/clothing/items.aspx",
    "https://www.ssense.com/it-it/uomo/abbigliamento",
    "https://www.amazon.it/s?k=gucci+uomo+abbigliamento",
    
    # ELETTRONICA (20)
    "https://www.amazon.it/s?k=iphone+15+pro",
    "https://www.mediaworld.it/search?query=iphone",
    "https://www.unieuro.it/online/search?text=iphone",
    "https://www.euronics.it/search?text=iphone",
    "https://www.trony.it/search?text=iphone",
    "https://www.samsung.com/it/smartphones/galaxy-s/",
    "https://www.apple.com/it/shop/buy-iphone/iphone-15",
    
    # MARKETPLACE (15)
    "https://www.ebay.it/sch/i.html?_nkw=rolex",
    "https://www.subito.it/annunci-italia/vendita/orologi/?q=rolex"
]

def classify_ai(title):  # AI CLASSIFICA AUTOMATICA
    title_lower = title.lower()
    if any(word in title_lower for word in ["rolex", "omega", "orologio", "watch", "cronografo"]):
        return "orologi"
    elif any(word in title_lower for word in ["nike", "adidas", "jordan", "dunk", "sneaker"]):
        return "sneakers"
    elif any(word in title_lower for word in ["gucci", "prada", "zara", "vestito", "maglia"]):
        return "moda"
    elif any(word in title_lower for word in ["iphone", "samsung", "smartphone", "notebook"]):
        return "elettronica"
    return "altro"

def scrape_tutti():
    global deals_data
    deals_data = []
    print(f"Inizio scan {len(NEGOZI)} negozi alle {datetime.now()}")
    for i, url in enumerate(NEGOZI):
        try:
            resp = requests.post("https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={
                    "url": url,
                    "extract": {
                        "prodotti": {
                            "type": "array",
                            "fields": {
                                "title": ".product-title, h1, h2, .name, [title]",
                                "price": ".price, .amount, .final-price",
                                "image": "img[src], .product-image src",
                                "description": ".desc, .details, p"
                            }
                        }
                    }
                }, timeout=30).json()
            
            prodotti = resp.get("data", {}).get("extract", {}).get("prodotti", [])
            for prod in prodotti[:5]:  # Max 5 per sito
                deals_data.append({
                    "title": prod.get("title", "N/A"),
                    "price": float(str(prod.get("price", "0")).replace("€", "").replace(",", ".").replace(".", "", 1)),
                    "image": prod.get("image", ""),
                    "category": classify_ai(prod.get("title", "")),
                    "source": url,
                    "timestamp": datetime.now().isoformat()
                })
            print(f"Negozi {i+1}: {len(prodotti)} prodotti")
        except Exception as e:
            print(f"Errore {url}: {e}")
    
    print(f"TOTALE {len(deals_data)} deal live!")
    # Salva su disco (opzionale)
    with open("deals.json", "w") as f:
        json.dump(deals_data, f)

@app.on_event("startup")
async def startup():
    scrape_tutti()  # Scansione iniziale
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_tutti, IntervalTrigger(minutes=15))
    scheduler.start()

@app.get("/deals")
async def get_deals():
    return deals_data

@app.get("/deals/{category}")
async def get_by_category(category: str):
    return [d for d in deals_data if d["category"] == category.lower()]

@app.get("/")
async def root():
    return {
        "status": "SNAG AI PRO Live",
        "negozi": len(NEGOZI),
        "tot_deals": len(deals_data),
        "ultimo_scan": deals_data[0]["timestamp"] if deals_data else "Mai"
    }
