
import requests

def check_2026():
    # 1. Check Football-Data 25/26
    print("--- Check Football-Data 25/26 ---")
    urls_fd = [
        'https://www.football-data.co.uk/mmz4281/2526/SP2.csv',
        'https://www.football-data.co.uk/mmz4281/2526/E1.csv',
        'https://www.football-data.co.uk/mmz4281/2526/SP1.csv'
    ]
    for url in urls_fd:
        try:
            r = requests.head(url, verify=False, timeout=5)
            print(f"{url}: {r.status_code}")
        except Exception as e:
            print(f"{url}: Error {e}")

    # 2. Check FixtureDownload 2026
    print("\n--- Check FixtureDownload 2026 ---")
    base = "https://fixturedownload.com/download"
    slugs = [
        'segunda-division-2026',
        'la-liga-2026',
        'premier-league-2026',
        'championship-2026',
        'segunda-division-2025-2026'
    ]
    for slug in slugs:
        url = f"{base}/{slug}-GMTStandardTime.csv"
        try:
            r = requests.head(url, verify=False, timeout=5)
            if r.status_code == 200:
                print(f"[SUCCESS] {slug}")
            else:
                print(f"[FAIL] {slug}: {r.status_code}")
        except Exception as e:
            print(f"{slug}: Error {e}")

if __name__ == "__main__":
    check_2026()
