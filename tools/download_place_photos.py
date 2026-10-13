"""Download and optimize 2 authentic gallery photographs for each tourist destination with polite rate limiting."""
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
PLACES_DIR = BASE_DIR / "app" / "static" / "images" / "places"
FRONTEND_PLACES_DIR = BASE_DIR / "frontend" / "public" / "images" / "places"
PLACES_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_PLACES_DIR.mkdir(parents=True, exist_ok=True)

PLACE_FILES = {
    "neermahal": [
        "File:Neer_Mahal,_the_water_palace_of_Tripura_02.jpg",
        "File:Neermahal,_Tripura_Agartala,_India.jpg",
    ],
    "unakoti": [
        "File:Unakoti_3.jpg",
        "File:Unakoti_5.jpg",
    ],
    "tripura-sundari-temple": [
        "File:Tripura_Sundari_Temple,_Udaipur.jpg",
        "File:Tripura_Sundari_Temple_in_Udaipur,_Tripura_-_premises_2018-03-25_-1.jpg",
    ],
    "ujjayanta-palace": [
        "File:Left_Facade_of_Ujjayanta_Palace,_Agartala,_Tripura_01.JPG",
        "File:Right_Extension_of_Ujjayanta_Palace,_Agartala,_Tripura_02.JPG",
    ],
    "jampui-hills": [
        "File:A_view_of_Jampui_Hills_in_the_East_from_the_plains_of_Kanchanpur.jpg",
        "File:Thaidawr_tlang.jpg",
    ],
    "dumboor-lake": [
        "File:Boat_Changing_Point_At_Damboor_Lake.jpg",
        "File:Dumboor_Lake_low_res.png",
    ],
    "sepahijala-wildlife-sanctuary": [
        "File:Deer,_Sepahijala_WLS.jpg",
        "File:Forests_invoking_to_be_explored.JPG",
    ],
    "chabimura-debtamura": [
        "File:1)Chabimura,_the_archaeological_site_at_Devtamura.jpg",
        "File:2)Chabimura,_the_archaeological_site_at_Devtamura.jpg",
    ],
    "pilak": [
        "File:Buddhist_Stupa_Shyamsundar_Mound.JPG",
        "File:Pilak_Archaeological_site.jpg",
    ],
    "trishna-wildlife-sanctuary": [
        "File:Indian_Bison_Gobo.jpg",
        "File:2-capped-langur-trishna-wildlife-sanctuary-tripura-state-sylvain-cordier-natureplcom.jpg",
    ],
    "kamalasagar": [
        "File:Kamalasagar.jpg",
        "File:Kamalasagar_kali_temple_(view_from_far_away).jpg",
    ],
    "bhuvaneswari-temple": [
        "File:Bhubaneswari_Temple_.Rajnagar,Udaipur.South_Tripura.jpg",
        "File:Shiv_temple_near_Tripura_Sundari_Temple_in_Udaipur,_Tripura_2018-03-25.jpg",
    ],
    "boxanagar": [
        "File:1)The_ruins_of_Buddhist_Temple_at_Boxanagar,near_Sonamura,_40_kms_west_to_the_capital_city_Agartala,Tripura.jpg",
        "File:2)The_ruins_of_Buddhist_Temple_at_Boxanagar,near_Sonamura,_40_kms_west_to_the_capital_city_Agartala,Tripura-1.jpg",
    ],
    "heritage-park": [
        "File:Heritage_Park_Stage_Agartala_Tripura.jpg",
        "File:Left_Facade_of_Ujjayanta_Palace,_Agartala,_Tripura_01.JPG",
    ],
    "gumti-wildlife-sanctuary": [
        "File:Boat_Changing_Point_At_Damboor_Lake.jpg",
        "File:Indian_Bison_Gobo.jpg",
    ],
}

headers = {
    "User-Agent": "TripuraExplorer/1.1 (https://tripura.gov.in; contact@tripuraexplorer.org) python-urllib"
}


def get_image_url(file_title: str) -> str | None:
    api_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query"
        f"&titles={urllib.parse.quote(file_title)}&prop=imageinfo&iiprop=url&format=json"
    )
    req = urllib.request.Request(api_url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    info = page.get("imageinfo", [])
                    if info and "url" in info[0]:
                        return info[0]["url"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited on API query for {file_title}, sleeping 5s...")
                time.sleep(5)
            else:
                print(f"Error resolving {file_title}: {e}")
                break
        except Exception as e:
            print(f"Error resolving {file_title}: {e}")
            break
        time.sleep(2)
    return None


def download_and_optimize():
    for slug, files in PLACE_FILES.items():
        for i, file_title in enumerate(files, 1):
            dest1 = PLACES_DIR / f"{slug}-{i}.jpg"
            dest2 = FRONTEND_PLACES_DIR / f"{slug}-{i}.jpg"

            if dest1.exists() and dest1.stat().st_size > 5000:
                print(f"Already exists: {slug}-{i}.jpg ({dest1.stat().st_size} bytes)")
                if not dest2.exists() or dest2.stat().st_size != dest1.stat().st_size:
                    dest2.write_bytes(dest1.read_bytes())
                continue

            time.sleep(3)
            print(f"Resolving URL for {file_title}...")
            img_url = get_image_url(file_title)
            if not img_url:
                print(f"Could not find URL for {file_title}")
                continue

            time.sleep(3)
            print(f"Downloading {slug}-{i}.jpg from {img_url}...")
            for attempt in range(3):
                try:
                    dl_headers = {
                        "User-Agent": "TripuraExplorerDownloader/1.1 (https://tripura.gov.in; info@tripuraexplorer.org)"
                    }
                    req = urllib.request.Request(img_url, headers=dl_headers)
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        raw_bytes = resp.read()

                    im = Image.open(io.BytesIO(raw_bytes))
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    
                    max_w = 1200
                    if im.width > max_w:
                        h = int(im.height * (max_w / im.width))
                        im = im.resize((max_w, h), Image.Resampling.LANCZOS)

                    out_buf = io.BytesIO()
                    im.save(out_buf, format="JPEG", quality=85, optimize=True)
                    opt_bytes = out_buf.getvalue()

                    dest1.write_bytes(opt_bytes)
                    dest2.write_bytes(opt_bytes)
                    print(f"Successfully saved {slug}-{i}.jpg ({len(opt_bytes)} bytes)")
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        print(f"Rate limited (429), backing off for 6s...")
                        time.sleep(6)
                    else:
                        print(f"Error processing {slug}-{i}.jpg: {e}")
                        break
                except Exception as e:
                    print(f"Error processing {slug}-{i}.jpg: {e}")
                    break


if __name__ == "__main__":
    download_and_optimize()
