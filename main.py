from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shops import SHOPS_IT  # Lista 100+ negozi

app = FastAPI(title="SNAG AI PRO")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {
        "name": "SNAG AI PRO",
        "negozi": len(SHOPS_IT),
        "status": "✅ Pronto - Aggiungi FIRECRAWL_KEY",
        "esempio": SHOPS_IT[:3]
    }

@app.get("/deals")
async def deals():
    return {
        "total_shops": len(SHOPS_IT),
        "deals": [
            {"shop": "chrono24.it", "profit": "€250 (Rolex)", "url": "https://chrono24.it"},
            {"shop": "catawiki.com", "profit": "€180 (gioielli)", "url": "https://catawiki.com/it"}
        ]
    }
