import time
import requests
import json
import os
from bs4 import BeautifulSoup
from html import escape


def fix_text(text):
    """Try to repair common mojibake/encoding issues like â or â."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def save_html(matches, filename="suretips.html"):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Sure Tips Predictions</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                padding: 20px;
                margin: 0;
            }
            h1 {
                color: #1565c0;
            }
            .date {
                font-size: 20px;
                font-weight: bold;
                color: #1565c0;
                margin-top: 24px;
                margin-bottom: 10px;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.12);
            }
            .match {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 6px;
            }
            .small {
                color: #555;
                margin-top: 4px;
            }
            .prediction {
                margin-top: 8px;
                font-weight: bold;
                color: #222;
            }
            .status {
                margin-top: 8px;
                font-weight: bold;
                color: #008000;
            }
            .pending {
                color: #d97706;
            }
            .lost {
                color: #dc2626;
            }
            .won {
                color: #16a34a;
            }
        </style>
    </head>
    <body>
        <h1>Sure Tips Predictions</h1>
    """

    def status_class(status_text):
        s = status_text.lower()
        if "pending" in s:
            return "pending"
        if "❌" in s or "lose" in s or "lost" in s:
            return "lost"
        return "won"

    current_date = None
    for m in matches:
        date = escape(fix_text(m.get("date", "N/A")))
        match = escape(fix_text(m.get("match", "N/A")))
        match_time = escape(fix_text(m.get("time", "N/A")))
        league = escape(fix_text(m.get("league", "N/A")))
        prediction = escape(fix_text(m.get("prediction", "N/A")))
        odds = escape(fix_text(m.get("odds", "N/A")))
        status = escape(fix_text(m.get("status", "N/A")))

        if date != current_date:
            current_date = date
            html += f'<div class="date">{date}</div>'

        css_class = status_class(status)

        html += f"""
        <div class="card">
            <div class="match">{match}</div>
            <div class="small">{match_time} | {league}</div>
            <div class="prediction">Prediction: {prediction}</div>
            <div class="small">Odds: {odds}</div>
            <div class="status {css_class}">Status: {status}</div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def scrape_vip_matches():
    current_time = int(time.time())
    url = f"https://html.e-droid.net/html/get_html.php?ida=2941533&ids=29769675&fum={current_time}"

    headers = {
        "User-Agent": "Android Vinebre Software",
        "Host": "html.e-droid.net",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Connection error: {e}")
        return

    if response.status_code != 200:
        print(f"Failed with status: {response.status_code}")
        return

    clean_html = response.text.replace("@MNQ@", "<").strip("[]")
    soup = BeautifulSoup(clean_html, "html.parser")

    json_file = "suretips.json"
    html_file = "suretips.html"
    match_db = {}

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                existing_list = json.load(f)
                for m in existing_list:
                    unique_id = f"{m['date']}_{m['match']}"
                    match_db[unique_id] = m
            except json.JSONDecodeError:
                pass

    current_date = None
    latest_date = None
    new_matches_count = 0
    updated_matches_count = 0

    for tag in soup.find_all(["h3", "div"]):
        if tag.name == "h3":
            current_date = fix_text(tag.text.strip())

            if latest_date is None:
                latest_date = current_date
                print(f"\n--- TODAY'S MATCHES ({latest_date}) ---")

        elif tag.name == "div" and "box" in tag.get("class", []):
            league = fix_text(tag.find("h2").text.strip()) if tag.find("h2") else "N/A"

            li = tag.find("li")
            time_span = li.find("span") if li else None
            match_time = fix_text(time_span.text.strip()) if time_span else "N/A"
            odds = fix_text(li.text.replace(match_time, "").strip()) if li else "N/A"

            match_name = fix_text(tag.find("h4").text.strip()) if tag.find("h4") else "N/A"
            prediction = fix_text(tag.find("h1").text.strip()) if tag.find("h1") else "N/A"
            status = fix_text(tag.find("p").text.strip()) if tag.find("p") else "N/A"

            match_data = {
                "date": current_date,
                "time": match_time,
                "league": league,
                "match": match_name,
                "prediction": prediction,
                "odds": odds,
                "status": status
            }

            unique_id = f"{current_date}_{match_name}"

            if unique_id not in match_db:
                match_db[unique_id] = match_data
                new_matches_count += 1
            else:
                if match_db[unique_id]["status"] != status:
                    match_db[unique_id]["status"] = status
                    updated_matches_count += 1

            if current_date == latest_date:
                print(f"⚽ {match_name} | Pick: {prediction} | Odds: {odds} | Status: {status}")

    all_matches = list(match_db.values())

    def parse_date_safe(item):
        try:
            return time.strptime(item["date"], "%d/%m/%y")
        except Exception:
            return time.gmtime(0)

    all_matches.sort(key=parse_date_safe, reverse=False)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=4, ensure_ascii=False)

    save_html(all_matches, html_file)

    print("-" * 50)
    print(f"✅ DB Saved to: {json_file}")
    print(f"✅ HTML Saved to: {html_file}")
    print(f"📊 Stats: {new_matches_count} New added | {updated_matches_count} Updated | {len(match_db)} Total in DB")


if __name__ == "__main__":
    scrape_vip_matches()