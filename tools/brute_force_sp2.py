
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def bf_sp2():
    base = "https://fixturedownload.com/download"
    slugs = [
        "segunda-division-2025",
        "la-liga-2-2025",
        "la-liga-2-2024",
        "spain-segunda-division-2025",
        "spain-segunda-2025",
        "segunda-2025",
        "liga-hypermotion-2025",
        "hypermotion-2025",
        "segunda-division-2024-2025",
        "la-liga-smartbank-2025",
        # Maybe it's just the old one if year is weird?
        "segunda-division-2024"
    ]
    
    print(f"Testing {len(slugs)} slugs on {base}...")
    headers = {'User-Agent': 'Mozilla/5.0'}

    for s in slugs:
        url = f"{base}/{s}-GMTStandardTime.csv"
        try:
            r = requests.head(url, verify=False, headers=headers, timeout=2)
            if r.status_code == 200:
                print(f"[SUCCESS] {s}")
                # Double check content
                r2 = requests.get(url, verify=False, headers=headers, stream=True)
                print(f"   Content-Type: {r2.headers.get('Content-Type')}")
                if b'Match Number' in r2.content[:100]:
                     print("   Verified CSV structure.")
            else:
                pass # print(f"[FAIL] {s}: {r.status_code}")
        except:
            pass
            
    print("Done.")

if __name__ == "__main__":
    bf_sp2()
