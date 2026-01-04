
import requests
import pandas as pd
import io
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def verify_fd_source():
    # URL pattern for 25/26 season (implied by user)
    url = "https://www.football-data.co.uk/mmz4281/2526/SP2.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print(f"Attempting to download: {url}")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            print("Download successful!")
            df = pd.read_csv(io.StringIO(r.content.decode('latin-1')))
            print(f"Columns: {list(df.columns)[:5]}")
            
            if 'Date' in df.columns:
                df['DateObj'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                today = pd.Timestamp.now().normalize()
                print(f"Today: {today}")
                
                # Check for future matches
                # In football-data.co.uk, fixtures usually have empty FTHG/FTAG
                # Or just date > today
                future = df[df['DateObj'] >= today]
                print(f"Future matches (>= Today): {len(future)}")
                
                if not future.empty:
                    print(future[['Date', 'HomeTeam', 'AwayTeam']].head())
                else:
                    print("No future matches found.")
                    print("Last 5 rows in DF:")
                    print(df[['Date', 'HomeTeam', 'AwayTeam']].tail(5))
                    print("Date format in file (first 5):")
                    print(df['Date'].head(5))
                    
                    # Check max date
                    print(f"Max Date in file: {df['DateObj'].max()}")
            
        else:
            print("Failed to download (Non-200).")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_fd_source()
