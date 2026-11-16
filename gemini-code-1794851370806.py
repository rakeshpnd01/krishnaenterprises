import glob
import json
import os
import re
import time
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# Verified baseline catalog for instant accuracy & fallback when Amazon/Flipkart rate-limits CI runners
VERIFIED_BASELINE = {
    "iqoo z11 5g": {
        "price": 39999, "mrp": 42999, "colorHex": "#10b981", "renderType": "phone-triple-ring",
        "imageUrl": "https://m.media-amazon.com/images/I/61+Q6Rh3OQL._SX679_.jpg",
        "highlights": [
            "MediaTek Dimensity 7500 Turbo 5G (1.2Mn+ AnTuTu)",
            "6.78\" 1.5K 144Hz 3D Curved AMOLED (2000 nits HBM)",
            "7050mAh BlueVolt Ultra-Slim Battery + 3800mm² VC Cooling",
            "50MP Sony IMX882 OIS Main + 32MP 4K Selfie + IP68/IP69"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 7500 Turbo (4nm)",
            "Display": "1.5K 144Hz 3D Curved AMOLED",
            "Battery": "7050mAh BlueVolt Durability",
            "Camera": "50MP Sony IMX882 OIS + 8MP UW | 32MP Front",
            "Protection": "IP68 & IP69 Dust/Water Resistant"
        }
    },
    "iqoo z11xa 5g": {
        "price": 28998, "mrp": 31999, "colorHex": "#34d399", "renderType": "phone-squircle",
        "imageUrl": "https://m.media-amazon.com/images/I/61VuVU94RnL._SX679_.jpg",
        "highlights": [
            "Dimensity 7400 Turbo Chipset (890K+ AnTuTu Score)",
            "Massive 7200mAh Battery + 44W FlashCharge & Bypass Charging",
            "50MP Sony IMX852 Ultra-HD + 32MP 4K Front Camera",
            "OriginOS 6 with AI Captions, Monster Mode & 4D Vibration"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 7400 Turbo",
            "Battery": "7200mAh + 44W FlashCharge",
            "Camera": "50MP Sony IMX852 + 32MP 4K Front",
            "OS": "OriginOS 6 (2 Yrs OS + 4 Yrs Security)"
        }
    },
    "iqoo z11 lite": {
        "price": 17499, "mrp": 19999, "colorHex": "#1d4ed8", "renderType": "phone-dual-pill",
        "imageUrl": "https://m.media-amazon.com/images/I/619VJYtpgaL._SX679_.jpg",
        "highlights": [
            "6500mAh High-Density Battery with 44W FlashCharge",
            "MediaTek Dimensity 6300 5G Processor + OriginOS 6.0",
            "6.74\" 120Hz Immersive Punch-Hole Display",
            "50MP Ultra-Clear AI Camera + IP65 Dust & Splash Resistance"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 6300 5G",
            "Display": "6.74-inch 120Hz HD+ Display",
            "Battery": "6500mAh + 44W Fast Charger in Box",
            "Protection": "IP65 Rated Protection"
        }
    },
    "ai+ nova 2 pro": {
        "price": 17999, "mrp": 19999, "colorHex": "#2563eb", "renderType": "phone-glyph-ring",
        "imageUrl": "",
        "highlights": [
            "MediaTek Dimensity 7100 5G Octa-Core Processor",
            "Customisable Back Panel LED Notification & Call Lights",
            "48MP Sony IMX582 Rear Camera + 13MP Clear Selfie",
            "6000mAh Battery • Android 16 with nxtQ OS"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 7100 5G",
            "Camera": "48MP Sony IMX582 Rear + 13MP Front",
            "Battery": "6000mAh Long-Lasting Battery",
            "OS": "Android 16 with nxtQ OS"
        }
    },
    "ai+ nova 2 power": {
        "price": 17999, "mrp": 20499, "colorHex": "#0ea5e9", "renderType": "phone-triple-ring",
        "imageUrl": "",
        "highlights": [
            "Massive 7000mAh Power-Series Battery with Fast Charging",
            "6.78\" 120Hz FHD+ Punch-Hole Smooth Display",
            "50MP AI Dual Rear Camera + 16MP Front Camera",
            "5G Dual SIM + Android 16 nxtQ Clean Experience"
        ],
        "specs": {
            "Battery": "7000mAh Power Cell",
            "Display": "6.78-inch 120Hz FHD+",
            "Camera": "50MP AI Dual + 16MP Front",
            "OS": "Android 16 with nxtQ OS"
        }
    },
    "ai+ nova 2 ultra": {
        "price": 22999, "mrp": 25999, "colorHex": "#0f172a", "renderType": "phone-pro-island",
        "imageUrl": "",
        "highlights": [
            "Flagship Curved 120Hz AMOLED Display + In-Display Fingerprint",
            "High-Speed 5G Dimensity Processor + Vapor Cooling",
            "64MP OIS Ultra-Night Camera + 32MP Portrait Selfie",
            "6000mAh Battery + Fast Charger Included in Box"
        ],
        "specs": {
            "Display": "Curved 120Hz AMOLED",
            "Camera": "64MP OIS Main + 32MP Selfie",
            "Battery": "6000mAh Fast Charging",
            "OS": "Android 16 with nxtQ OS"
        }
    },
    "ai+ nova 2 neo": {
        "price": 15999, "mrp": 17999, "colorHex": "#f97316", "renderType": "phone-squircle",
        "imageUrl": "",
        "highlights": [
            "Vibrant Multi-Color Edition • 5G Dual SIM Connectivity",
            "120Hz Punch-Hole Smooth Display",
            "50MP AI Camera System + 6000mAh All-Day Battery",
            "Android 16 with nxtQ Privacy & Smart Tools"
        ],
        "specs": {
            "Battery": "6000mAh Long-Lasting Battery",
            "Camera": "50MP Rear AI Camera",
            "OS": "Android 16 with nxtQ OS"
        }
    },
    "ai+ nova 2 5g": {
        "price": 14999, "mrp": 16999, "colorHex": "#3b82f6", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "Unisoc T8200 5G Octa-Core Processor (510K+ AnTuTu)",
            "6.75\" 120Hz Smooth Refresh Rate Display",
            "50MP AI Dual Rear Camera + 6000mAh Battery",
            "Includes Charger, TPU Case & Screen Film in Box"
        ],
        "specs": {
            "Processor": "Unisoc T8200 5G Octa-Core",
            "Battery": "6000mAh Lithium Polymer",
            "Camera": "50MP AI Dual Camera"
        }
    },
    "ai+ pulse 2": {
        "price": 11499, "mrp": 14999, "colorHex": "#18181b", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "6.745\" HD+ Punch-Hole Display + Side Fingerprint Sensor",
            "Unisoc T7250 Octa-Core Processor + Expandable Storage",
            "50MP Rear Camera with LED Flash + 8MP Front Camera",
            "6000mAh Battery + IP64 Splash Resistance + Android 16"
        ],
        "specs": {
            "Display": "6.745-inch HD+ Punch-Hole",
            "Battery": "6000mAh + Charger in Box",
            "Protection": "IP64 Dust & Splash Resistant"
        }
    },
    "vivo t5x": {
        "price": 27999, "mrp": 30999, "colorHex": "#059669", "renderType": "phone-squircle",
        "imageUrl": "",
        "highlights": [
            "MediaTek Dimensity 7400-Turbo Octa-Core 5G Processor",
            "Massive 7200mAh Ultra-Endurance Battery for 2-Day Backup",
            "50MP + 2MP Dual Rear Camera + 32MP HD Selfie Camera",
            "120Hz Punch-Hole Display + 1 Year Official vivo Warranty"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 7400-Turbo",
            "Battery": "7200mAh High-Density Battery",
            "Camera": "50MP + 2MP Rear | 32MP Front"
        }
    },
    "vivo y21": {
        "price": 27999, "mrp": 29999, "colorHex": "#2563eb", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "MediaTek Dimensity 6300 5G Efficient Processor",
            "6500mAh BlueVolt Long-Life Battery + Fast Charging",
            "50MP AI Night Portrait Camera + Stylish Slim Body",
            "Official vivo India Warranty + In-Store EMI Support"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 6300 5G",
            "Battery": "6500mAh Long-Lasting Battery",
            "Camera": "50MP Rear Camera"
        }
    },
    "vivo y11": {
        "price": 19999, "mrp": 22499, "colorHex": "#1e3a8a", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "Reliable 5G Connectivity with Smooth Eye-Care Display",
            "All-Day Long-Lasting Battery + Smart Charging Engine",
            "50MP AI Clear Camera + Sleek Scratch-Resistant Finish",
            "Official vivo Distributor Unit with Full GST Invoice"
        ],
        "specs": {
            "Network": "Dual 5G SIM Support",
            "Warranty": "1 Year Official vivo India Warranty"
        }
    },
    "oneplus n6": {
        "price": 23049, "mrp": 26999, "colorHex": "#34d399", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "Segment-Leading 8000mAh Battery + 45W SUPERVOOC Fast Charging",
            "MediaTek Dimensity 6360 Apex 5G Processor + OxygenOS 16.0",
            "6.8\" 120Hz Display + MIL-STD-810H Military Durability",
            "50MP Main Camera + 7-Year Battery Health Engine"
        ],
        "specs": {
            "Battery": "8000mAh + 45W SUPERVOOC",
            "Processor": "MediaTek Dimensity 6360 Apex 5G",
            "OS": "OxygenOS 16.0"
        }
    },
    "redmi note 15 se": {
        "price": 25999, "mrp": 28999, "colorHex": "#18181b", "renderType": "phone-squircle",
        "imageUrl": "",
        "highlights": [
            "6.77\" 120Hz 3D Curved AMOLED Display with Vivid Colors",
            "Qualcomm Snapdragon 6 Gen 3 5G Octa-Core Processor",
            "5800mAh High-Density Battery + Fast Charger in Box",
            "IP65 & IP66 Dust and Water Protection + Dual Stereo Speakers"
        ],
        "specs": {
            "Processor": "Qualcomm Snapdragon 6 Gen 3 5G",
            "Display": "6.77-inch Curved AMOLED",
            "Battery": "5800mAh Long-Lasting Battery"
        }
    },
    "motorola g37 power": {
        "price": 16999, "mrp": 19499, "colorHex": "#0284c7", "renderType": "phone-squircle",
        "imageUrl": "",
        "highlights": [
            "Massive 7000mAh Battery + 33W TurboPower Charger Included",
            "MediaTek Dimensity 6400 5G Processor + Clean Android 16",
            "6.7\" 120Hz Display with Stereo Dolby Atmos Speakers",
            "50MP Quad Pixel Camera + PANTONE Capri Vegan Leather Finish"
        ],
        "specs": {
            "Processor": "MediaTek Dimensity 6400 5G",
            "Battery": "7000mAh + 33W TurboPower Charger",
            "OS": "Android 16"
        }
    },
    "infinix hot 60i": {
        "price": 15999, "mrp": 17999, "colorHex": "#1e293b", "renderType": "phone-triple-ring",
        "imageUrl": "",
        "highlights": [
            "6.75\" 120Hz Punch-Hole Display with Dynamic Bar",
            "6000mAh Marathon Battery with Fast Type-C Charging",
            "50MP AI Dual Camera + DTS Stereo Sound Enhancement",
            "5G Dual SIM Support + Sleek Matte Fingerprint-Free Back"
        ],
        "specs": {
            "Display": "6.75-inch 120Hz HD+ Display",
            "Battery": "6000mAh High-Capacity Battery"
        }
    },
    "tecno spark go3": {
        "price": 16999, "mrp": 18999, "colorHex": "#64748b", "renderType": "phone-pro-island",
        "imageUrl": "",
        "highlights": [
            "Basalt Titanium Metallic Frame + 120Hz Smooth Display",
            "50MP Ultra-Clear AI Camera + Dual LED Flash",
            "6000mAh Battery + Side-Mounted Fingerprint Unlock",
            "128GB Large Storage + Memory Fusion RAM Expansion"
        ],
        "specs": {
            "Design": "Basalt Titanium Finish",
            "Battery": "6000mAh All-Day Battery"
        }
    },
    "boltt ace": {
        "price": 15999, "mrp": 17999, "colorHex": "#881337", "renderType": "phone-dual-pill",
        "imageUrl": "",
        "highlights": [
            "T8200 Octa-Core 2.3GHz 5G Processor (5.47 Lakh+ AnTuTu)",
            "6.79\" 120Hz Punch-Hole Display + 64MP AI Night Camera",
            "6000mAh 2-Day Battery + Circle to Search AI Support",
            "3 Years Major Android Upgrades + 4 Years Security Updates"
        ],
        "specs": {
            "Processor": "T8200 Octa-Core 5G (2.3GHz)",
            "Battery": "6000mAh 2-Day Battery"
        }
    },
    "ambrane aerosync": {
        "price": 1599, "mrp": 2499, "colorHex": "#1d4ed8", "renderType": "powerbank-magsafe",
        "imageUrl": "",
        "highlights": [
            "Strong Magnetic Wireless Snap-On Charging (Up to 15W Qi)",
            "22.5W Fast Wired Output via USB Type-C PD & USB-A",
            "Compact 10000mAh Lithium Polymer • Flight Approved",
            "Works with iPhone 12–16 MagSafe & All Android Phones"
        ],
        "specs": {
            "Capacity": "10000mAh Li-Polymer",
            "Output": "15W Wireless + 22.5W Wired PD"
        }
    },
    "boat energyshroom": {
        "price": 1299, "mrp": 2999, "colorHex": "#dc2626", "renderType": "powerbank-slim",
        "imageUrl": "",
        "highlights": [
            "PB331: 15W Magnetic Wireless + 22.5W 2-Way Fast Charging",
            "PB300: 22.5W Dual USB-A + Type-C Pocket Power Bank",
            "12-Layer Smart IC Protection Against Short-Circuit & Overheat",
            "1 Year Official boAt India Manufacturer Warranty"
        ],
        "specs": {
            "Capacity": "10000mAh Li-Polymer",
            "Warranty": "1 Year boAt India Warranty"
        }
    }
}


def find_latest_excel():
    xlsx_files = [f for f in glob.glob("*.xlsx") if not f.startswith("~$")]
    if not xlsx_files:
        raise FileNotFoundError("No .xlsx stock file found in repository root.")
    xlsx_files.sort(key=os.path.getmtime, reverse=True)
    return xlsx_files[0]


def fetch_online_details(brand, model_name, variant):
    """Fetches live price, image, and highlights from Amazon.in (for iQOO) or Flipkart (others)."""
    is_iqoo = brand.strip().lower() == "iqoo"
    source = "Amazon.in" if is_iqoo else "Flipkart"
    domain = "amazon.in" if is_iqoo else "flipkart.com"
    query = f"site:{domain} {model_name} {variant}".strip()

    live_price = None
    live_image = None
    live_highlights = []

    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="in-en", max_results=3))
                for r in results:
                    snippet = f"{r.get('title', '')} {r.get('body', '')}"
                    price_match = re.search(r"₹\s?([0-9]{1,2},[0-9]{3})", snippet)
                    if price_match and not live_price:
                        parsed = int(price_match.group(1).replace(",", ""))
                        if 500 <= parsed <= 150000:
                            live_price = parsed

                    url = r.get("href", "")
                    if url and not live_image:
                        try:
                            resp = requests.get(url, headers=HEADERS, timeout=6)
                            if resp.status_code == 200:
                                soup = BeautifulSoup(resp.text, "html.parser")
                                if is_iqoo:
                                    img_tag = soup.select_one("#landingImage, img[data-old-hires]")
                                    if img_tag:
                                        live_image = img_tag.get("data-old-hires") or img_tag.get("src")
                                    bullets = [li.get_text(strip=True) for li in soup.select("#feature-bullets li span") if len(li.get_text(strip=True)) > 12]
                                    if bullets:
                                        live_highlights = bullets[:4]
                                else:
                                    img_tag = soup.select_one("img._396cs4, img._2r_T1I, img.DByuf4")
                                    if img_tag and img_tag.get("src"):
                                        live_image = img_tag.get("src")
                                    bullets = [li.get_text(strip=True) for li in soup.select("li._21Ahn-, li._7eSDEz") if len(li.get_text(strip=True)) > 10]
                                    if bullets:
                                        live_highlights = bullets[:4]
                        except Exception:
                            pass
            time.sleep(0.6)
        except Exception as exc:
            print(f"[WARN] Search lookup skipped for {model_name}: {exc}")

    return source, live_price, live_image, live_highlights


def guess_color_hex(variant_text):
    v = variant_text.lower()
    if "green" in v or "mint" in v:
        return "#10b981"
    if "blue" in v or "capri" in v:
        return "#2563eb"
    if "orange" in v or "flame" in v:
        return "#f97316"
    if "red" in v or "burgundy" in v:
        return "#dc2626"
    if "gold" in v:
        return "#d97706"
    if "titanium" in v or "silver" in v:
        return "#64748b"
    return "#1e293b"


def build_stock_json():
    excel_path = find_latest_excel()
    print(f"Reading active stock from: {excel_path}")

    df = pd.read_excel(excel_path, sheet_name="Master Order Log", skiprows=3)
    df = df[
        (df["Active Units / Lots"] > 0)
        & (df["Brand"].notna())
        & (~df["Brand"].astype(str).str.contains("TOTAL", case=False, na=False))
    ].copy()

    df["Brand"] = df["Brand"].astype(str).str.strip()
    df["Product Name"] = df["Product Name"].astype(str).str.strip()
    df["Variant / Details"] = df["Variant / Details"].fillna("Standard").astype(str).str.strip()
    df["Status"] = df["Status"].fillna("Delivered").astype(str).str.strip()

    grouped = df.groupby(["Brand", "Product Name", "Variant / Details", "Status"], as_index=False).agg(
        stock=("Active Units / Lots", "sum"),
        avg_cost=("Unit Price (INR)", "mean"),
    )

    products = []
    for idx, row in grouped.iterrows():
        brand = row["Brand"]
        if "miscellaneous" in brand.lower():
            brand = "Accessories"

        name = row["Product Name"]
        variant = row["Variant / Details"]
        stock_qty = int(row["stock"])
        cost = float(row["avg_cost"])
        status = "In Stock" if row["Status"].lower() == "delivered" else "In Transit"

        # Match baseline specs/highlights
        baseline = next((v for k, v in VERIFIED_BASELINE.items() if k in name.lower()), None)
        source, live_price, live_image, live_highlights = fetch_online_details(brand, name, variant)

        # Pricing priority: Live Scraped Price -> Verified Baseline Price -> Cost + 12% Margin
        if live_price:
            final_price = live_price
        elif baseline:
            final_price = baseline["price"]
            # Adjust variant pricing for 64GB vs 128GB where applicable
            if "64gb" in variant.lower() and "128gb" not in variant.lower() and final_price > 12000:
                final_price = max(int(round(cost * 1.12 / 100) * 100 - 1), final_price - 2500)
        else:
            final_price = int(round((cost * 1.12) / 100) * 100 - 1)

        mrp = baseline["mrp"] if baseline and baseline["mrp"] > final_price else final_price + 2500
        image_url = live_image or (baseline["imageUrl"] if baseline else "")
        highlights = live_highlights or (
            baseline["highlights"]
            if baseline
            else [
                f"Genuine {brand} Sealed Box Handset",
                f"Variant: {variant}",
                "Official Brand Service Center Warranty",
                "Available at Krishna Enterprises, Karela Bazar, Patti",
            ]
        )
        specs = (
            baseline["specs"]
            if baseline
            else {
                "Brand": brand,
                "Model": name,
                "Variant": variant,
                "Warranty": "1 Year Official Brand Warranty",
            }
        )

        products.append(
            {
                "id": f"KE-{idx + 1:03d}",
                "brand": brand,
                "name": name,
                "variant": variant,
                "colorHex": guess_color_hex(variant) if variant != "Standard" else (baseline["colorHex"] if baseline else "#1d4ed8"),
                "renderType": baseline["renderType"] if baseline else ("powerbank-slim" if "power bank" in name.lower() else "phone-dual-pill"),
                "price": final_price,
                "mrp": mrp,
                "source": source,
                "stock": stock_qty,
                "status": status,
                "eta": "Ready at Karela Bazar Counter" if status == "In Stock" else "Arriving Soon • Pre-Book Now",
                "imageUrl": image_url,
                "highlights": highlights,
                "specs": specs,
            }
        )

    payload = {
        "shopName": "Krishna Enterprises",
        "address": "Karela Bazar, Near PNB Bank, Patti Kohdaur Road, Patti - 230135, Uttar Pradesh",
        "whatsapp": "919930674906",
        "sourceFile": excel_path,
        "lastUpdated": datetime.now().strftime("%d %b %Y, %I:%M %p IST"),
        "products": products,
    }

    with open("stock_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated stock_data.json with {len(products)} active lines.")


if __name__ == "__main__":
    build_stock_json()