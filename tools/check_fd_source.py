
import pandas as pd
import requests
import io

def check_football_data():
    # 24/25 Season URLs
    urls = {
        'SP2': 'https://www.football-data.co.uk/mmz4281/2425/SP2.csv',
        'E1': 'https://www.football-data.co.uk/mmz4281/2425/E1.csv',
        'SP1': 'https://www.football-data.co.uk/mmz4281/2425/SP1.csv'
    }
    
    for league, url in urls.items():
        print(f"Checking {league}: {url}...")
        try:
            r = requests.get(url, verify=False, timeout=10)
            if r.status_code == 200:
                print(f"[SUCCESS] Downloaded {len(r.content)} bytes.")
                df = pd.read_csv(io.StringIO(r.content.decode('utf-8', errors='ignore')))
                print("Columns:", df.columns.tolist()[:10])
                
                if 'Date' in df.columns:
                    df['DateObj'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                    today = pd.Timestamp.now().normalize()
                    future = df[df['DateObj'] >= today]
                    
                    print(f"Total matches: {len(df)}")
                    print(f"Future matches (>= {today.date()}): {len(future)}")
                    
                    if not future.empty:
                        print(future[['Date', 'HomeTeam', 'AwayTeam']].head())
                    else:
                        print("No future matches found in this CSV.")
                else:
                    print("'Date' column missing.")
            else:
                print(f"[FAIL] Status {r.status_code}")
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    check_football_data()
