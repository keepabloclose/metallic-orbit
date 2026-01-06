import requests
import json
import os

API_KEY = "e9be0a4fb2370fa9a2b574fccd726c50da0aae8acfd94a4b6c286a92b62345a2"
BASE_URL = "https://api2.odds-api.io/v3"

def debug_structure():
    print("--- 1. Probing League Endpoints ---")
    
    # Trial 1: /leagues?sport=football
    url1 = f"{BASE_URL}/leagues?apiKey={API_KEY}&sport=football"
    print(f"Trial 1: {url1}")
    res1 = requests.get(url1)
    if res1.status_code == 200:
        leagues = res1.json()
        print("--- Spain Check ---")
        targets = ['spain', 'primera', 'laliga']
        
        with open("leagues_output_spain.txt", "w", encoding='utf-8') as f:
             for l in leagues:
                name = l.get('name', '').lower()
                slug = l.get('slug', '')
                for t in targets:
                    if t in name or t in slug:
                        print(f"Match: {l.get('name')} | Slug: {slug}")
                        f.write(f"Match: {l.get('name')} | Slug: {slug}\n")
                        break # Found one match
        return

if __name__ == "__main__":
    debug_structure()
