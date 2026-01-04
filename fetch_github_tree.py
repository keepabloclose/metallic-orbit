import requests
import re

def list_logos():
    print("--- FETCHING GITHUB LOGOS TREE ---")
    # Fetch La Liga Folder
    url = "https://github.com/luukhopman/football-logos/tree/master/logos/Spain%20-%20La%20Liga"
    
    try:
        r = requests.get(url)
        if r.status_code != 200:
            print(f"Failed to fetch {url}: {r.status_code}")
            return
            
        content = r.text
        # Naive regex to find .png files
        matches = re.findall(r'title="([^"]+\.png)"', content)
        
        print(f"Found {len(matches)} images in La Liga folder.")
        for m in matches:
            if "Getafe" in m or "Barcelona" in m or "Rayo" in m:
                print(f"  FOUND: {m}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_logos()
