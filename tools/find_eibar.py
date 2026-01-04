
import pandas as pd
import requests
import io

def find_eibar():
    url = "https://www.football-data.co.uk/mmz4281/2425/SP2.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8', errors='ignore')))
            print(f"Loaded {len(df)} rows.")
            
            # Normalize names for search
            # Eibar usually 'Eibar'. Mirandes usually 'Mirandes'.
            
            mask = (df['HomeTeam'].str.contains('Eibar', case=False, na=False)) & \
                   (df['AwayTeam'].str.contains('Mirandes', case=False, na=False))
                   
            match = df[mask]
            if not match.empty:
                print("FOUND MATCH!")
                print(match.to_string())
                # Check date
                d = match.iloc[0]['Date']
                print(f"Raw Date: {d}")
                d_obj = pd.to_datetime(d, dayfirst=True, errors='coerce')
                print(f"Parsed Date: {d_obj}")
            else:
                print("Match (Eibar vs Mirandes) NOT found.")
                print("Sample Eibar home games:")
                print(df[df['HomeTeam'].str.contains('Eibar', case=False, na=False)][['Date', 'HomeTeam', 'AwayTeam']].head())
        else:
            print(f"Failed to download: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_eibar()
