import time
import requests
import json
import os
from bs4 import BeautifulSoup
from html import escape


def fix_text(text):
    """Fix common mojibake/encoding issues like â or â."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def get_status_info(status_text):
    s = (status_text or "").lower()
    if "pending" in s:
        return ("pending", "Pending")
    if "❌" in status_text or "lose" in s or "lost" in s:
        return ("lost", "Lost")
    if "✅" in status_text or "won" in s or "win" in s:
        return ("won", "Won")
    return ("won", "Won")


def save_html(matches, filename="index.html"):
    def parse_date_safe(date_str):
        try:
            return time.strptime(date_str, "%d/%m/%y")
        except Exception:
            return time.gmtime(0)

    def build_grouped_sections(match_list):
        html_parts = []
        current_date = None

        for m in match_list:
            raw_date = fix_text(m.get("date", "N/A"))
            raw_match = fix_text(m.get("match", "N/A"))
            raw_time = fix_text(m.get("time", "N/A"))
            raw_league = fix_text(m.get("league", "N/A"))
            raw_prediction = fix_text(m.get("prediction", "N/A"))
            raw_odds = fix_text(m.get("odds", "N/A"))
            raw_status = fix_text(m.get("status", "N/A"))

            date = escape(raw_date)
            match = escape(raw_match)
            match_time = escape(raw_time)
            league = escape(raw_league)
            prediction = escape(raw_prediction)
            odds = escape(raw_odds)
            status = escape(raw_status)

            status_class, status_label = get_status_info(raw_status)

            if date != current_date:
                if current_date is not None:
                    html_parts.append("""
                            </div>
                        </section>
                    """)
                current_date = date
                html_parts.append(f"""
                    <section class="day-section">
                        <h2 class="day-title">📅 {date}</h2>
                        <div class="matches-grid">
                """)

            html_parts.append(f"""
                <article class="card match-card"
                    data-status="{status_class}"
                    data-match="{match.lower()}"
                    data-league="{league.lower()}"
                    data-prediction="{prediction.lower()}">
                    <div class="card-top">
                        <div class="match-wrap">
                            <h3 class="match">{match}</h3>
                            <div class="meta">
                                <span class="chip">🕒 {match_time}</span>
                                <span class="chip">🏆 {league}</span>
                            </div>
                        </div>

                        <div class="odds-box">
                            <div class="odds-label">Odds</div>
                            <div class="odds-value">{odds}</div>
                        </div>
                    </div>

                    <div class="prediction-block">
                        <div class="prediction-label">Prediction</div>
                        <div class="prediction-value">{prediction}</div>
                    </div>

                    <div class="footer-row">
                        <div class="status-pill {status_class}">
                            ● {status_label}
                        </div>
                        <div class="score-text">{status}</div>
                    </div>
                </article>
            """)

        if current_date is not None:
            html_parts.append("""
                    </div>
                </section>
            """)

        if not html_parts:
            return '<div class="empty-tab-msg">No matches in this section yet.</div>'

        return "".join(html_parts)

    all_matches = sorted(
        matches,
        key=lambda m: parse_date_safe(m.get("date", "")),
        reverse=True
    )

    unique_dates = []
    seen = set()
    for m in all_matches:
        d = m.get("date", "")
        if d not in seen:
            seen.add(d)
            unique_dates.append(d)

    latest_date = unique_dates[0] if len(unique_dates) > 0 else None
    second_latest_date = unique_dates[1] if len(unique_dates) > 1 else None

    today_matches = [m for m in all_matches if m.get("date") == latest_date]
    yesterday_matches = [m for m in all_matches if m.get("date") == second_latest_date]
    history_matches = [
        m for m in all_matches
        if m.get("date") not in {latest_date, second_latest_date}
    ]

    today_html = build_grouped_sections(today_matches)
    yesterday_html = build_grouped_sections(yesterday_matches)
    history_html = build_grouped_sections(history_matches)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
        <meta name="theme-color" content="#07111f">
        <title>Sure Tips Predictions</title>
        <style>
            :root {{
                --bg: #07111f;
                --bg-soft: #0d1728;
                --card: #0f1c30;
                --card-2: #12233b;
                --text: #eef3fb;
                --muted: #95a5bf;
                --line: rgba(255,255,255,0.08);
                --gold: #f4b321;
                --gold-soft: rgba(244, 179, 33, 0.14);
                --green: #1fce6d;
                --red: #ff5c74;
                --orange: #ffb84d;
                --shadow: 0 10px 30px rgba(0,0,0,0.28);
                --radius: 18px;
            }}

            * {{
                box-sizing: border-box;
            }}

            html {{
                scroll-behavior: smooth;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                color: var(--text);
                background:
                    radial-gradient(circle at top center, rgba(244,179,33,0.10), transparent 24%),
                    linear-gradient(180deg, #06101d 0%, #091322 100%);
                min-height: 100vh;
            }}

            .app-shell {{
                max-width: 760px;
                margin: 0 auto;
                padding-bottom: 96px;
            }}

            .topbar {{
                position: sticky;
                top: 0;
                z-index: 40;
                backdrop-filter: blur(10px);
                background: rgba(7, 17, 31, 0.88);
                border-bottom: 1px solid var(--line);
                padding: 14px 16px 12px;
            }}

            .brand-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
            }}

            .brand {{
                display: flex;
                align-items: center;
                gap: 12px;
                min-width: 0;
            }}

            .logo {{
                width: 42px;
                height: 42px;
                border-radius: 14px;
                background: linear-gradient(135deg, var(--gold), #ffd36f);
                color: #131313;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                box-shadow: 0 8px 20px rgba(244,179,33,0.28);
                flex-shrink: 0;
            }}

            .brand-text {{
                min-width: 0;
            }}

            .brand-title {{
                font-size: 20px;
                font-weight: 800;
                line-height: 1.1;
                margin: 0;
                color: #ffffff;
                letter-spacing: 0.2px;
            }}

            .brand-subtitle {{
                margin-top: 4px;
                color: var(--muted);
                font-size: 12px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .hero {{
                padding: 18px 16px 12px;
            }}

            .hero-card {{
                border: 1px solid rgba(244,179,33,0.16);
                background:
                    radial-gradient(circle at top right, rgba(244,179,33,0.12), transparent 35%),
                    linear-gradient(180deg, rgba(18,35,59,0.95), rgba(11,21,36,0.95));
                border-radius: 22px;
                padding: 18px;
                box-shadow: var(--shadow);
            }}

            .badge {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 12px;
                border-radius: 999px;
                color: var(--gold);
                background: var(--gold-soft);
                border: 1px solid rgba(244,179,33,0.18);
            }}

            .hero h1 {{
                margin: 14px 0 8px;
                font-size: 30px;
                line-height: 1.08;
                font-weight: 800;
                letter-spacing: -0.6px;
            }}

            .hero h1 .accent {{
                color: var(--gold);
            }}

            .hero p {{
                margin: 0;
                color: var(--muted);
                font-size: 14px;
                line-height: 1.55;
            }}

            .nav-tabs {{
                display: flex;
                gap: 10px;
                padding: 4px 16px 8px;
                overflow-x: auto;
                scrollbar-width: none;
            }}

            .nav-tabs::-webkit-scrollbar {{
                display: none;
            }}

            .nav-tab {{
                border: 1px solid var(--line);
                background: rgba(255,255,255,0.03);
                color: var(--muted);
                border-radius: 999px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 800;
                cursor: pointer;
                white-space: nowrap;
                transition: 0.18s ease;
            }}

            .nav-tab.active {{
                background: var(--gold-soft);
                color: var(--gold);
                border-color: rgba(244,179,33,0.24);
            }}

            .tools {{
                padding: 4px 16px 14px;
            }}

            .search-wrap {{
                display: flex;
                gap: 10px;
                align-items: center;
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 12px 14px;
                margin-bottom: 12px;
            }}

            .search-wrap span {{
                color: var(--muted);
                font-size: 16px;
            }}

            .search-input {{
                width: 100%;
                background: transparent;
                border: 0;
                outline: 0;
                color: var(--text);
                font-size: 14px;
            }}

            .search-input::placeholder {{
                color: #7e90ad;
            }}

            .filters {{
                display: flex;
                gap: 10px;
                overflow-x: auto;
                padding-bottom: 4px;
                scrollbar-width: none;
            }}

            .filters::-webkit-scrollbar {{
                display: none;
            }}

            .filter-btn {{
                border: 1px solid var(--line);
                background: rgba(255,255,255,0.03);
                color: var(--muted);
                border-radius: 999px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
                white-space: nowrap;
                transition: 0.18s ease;
            }}

            .filter-btn.active {{
                background: var(--gold-soft);
                color: var(--gold);
                border-color: rgba(244,179,33,0.24);
            }}

            .tab-panel {{
                display: none;
            }}

            .tab-panel.active {{
                display: block;
            }}

            .content {{
                padding: 0 16px;
            }}

            .day-section {{
                margin-top: 18px;
            }}

            .day-title {{
                position: sticky;
                top: 128px;
                z-index: 10;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin: 0 0 12px;
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(8,16,28,0.88);
                backdrop-filter: blur(10px);
                border: 1px solid var(--line);
                color: var(--gold);
                font-size: 14px;
                font-weight: 800;
            }}

            .matches-grid {{
                display: grid;
                gap: 12px;
            }}

            .card {{
                background: linear-gradient(180deg, rgba(17,29,49,0.98), rgba(13,23,40,0.98));
                border: 1px solid var(--line);
                border-radius: var(--radius);
                padding: 10px;
                box-shadow: var(--shadow);
            }}

            .card-top {{
                display: flex;
                gap: 12px;
                justify-content: space-between;
                align-items: flex-start;
            }}

            .match-wrap {{
                min-width: 0;
                flex: 1;
            }}

            .match {{
                margin: 0;
                font-size: 18px;
                line-height: 1.25;
                font-weight: 800;
                color: #ffffff;
                word-break: break-word;
            }}

            .meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-top: 8px;
                color: var(--muted);
                font-size: 13px;
            }}

            .chip {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 9px;
                border-radius: 999px;
                background: rgba(255,255,255,0.04);
                border: 1px solid var(--line);
                color: var(--muted);
                font-size: 12px;
                font-weight: 700;
            }}

            .odds-box {{
                flex-shrink: 0;
                min-width: 74px;
                text-align: center;
                border-radius: 14px;
                padding: 10px 10px;
                background: linear-gradient(180deg, rgba(244,179,33,0.18), rgba(244,179,33,0.08));
                border: 1px solid rgba(244,179,33,0.18);
            }}

            .odds-label {{
                color: #d9b65c;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .odds-value {{
                margin-top: 5px;
                color: var(--gold);
                font-size: 20px;
                font-weight: 800;
            }}

            .prediction-block {{
                margin-top: 10px;
                padding: 9px 12px;
                border-radius: 14px;
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--line);
            }}

            .prediction-label {{
                color: var(--muted);
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.7px;
            }}

            .prediction-value {{
                margin-top: 4px;
                color: #fff;
                font-size: 17px;
                font-weight: 800;
                line-height: 1.2;
            }}

            .footer-row {{
                margin-top: 10px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                flex-wrap: wrap;
            }}

            .status-pill {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 800;
                border: 1px solid transparent;
            }}

            .status-pill.pending {{
                color: var(--orange);
                background: rgba(255,184,77,0.12);
                border-color: rgba(255,184,77,0.18);
            }}

            .status-pill.won {{
                color: var(--green);
                background: rgba(31,206,109,0.12);
                border-color: rgba(31,206,109,0.16);
            }}

            .status-pill.lost {{
                color: var(--red);
                background: rgba(255,92,116,0.12);
                border-color: rgba(255,92,116,0.16);
            }}

            .score-text {{
                color: var(--muted);
                font-size: 13px;
                font-weight: 700;
            }}

            .empty-state {{
                display: none;
                margin-top: 24px;
                padding: 22px;
                text-align: center;
                border-radius: 18px;
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--line);
                color: var(--muted);
            }}

            .empty-tab-msg {{
                margin-top: 18px;
                padding: 22px;
                text-align: center;
                border-radius: 18px;
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--line);
                color: var(--muted);
            }}

            .bottom-pad {{
                height: 24px;
            }}

            @media (max-width: 520px) {{
                .hero h1 {{
                    font-size: 26px;
                }}

                .card {{
                    padding: 12px;
                }}

                .match {{
                    font-size: 17px;
                }}

                .prediction-value {{
                    font-size: 16px;
                }}

                .day-title {{
                    top: 184px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="app-shell">
            <div class="topbar">
                <div class="brand-row">
                    <div class="brand">
                        <div class="logo">⚽</div>
                        <div class="brand-text">
                            <div class="brand-title">Sure Tips</div>
                            <div class="brand-subtitle">Cloud predictions dashboard</div>
                        </div>
                    </div>
                </div>
            </div>

            <section class="hero">
                <div class="hero-card">
                    <div class="badge">★ Live predictions</div>
                    <h1>Track your <span class="accent">daily picks</span> like an app.</h1>
                    <p>Browse current results faster with Today, Yesterday, and History tabs while keeping search and filters.</p>
                </div>
            </section>

            <section class="nav-tabs">
                <button class="nav-tab active" data-tab="todayPanel">Today</button>
                <button class="nav-tab" data-tab="yesterdayPanel">Yesterday</button>
                <button class="nav-tab" data-tab="historyPanel">History</button>
            </section>

            <section class="tools">
                <div class="search-wrap">
                    <span>🔎</span>
                    <input id="searchInput" class="search-input" type="text" placeholder="Search match, league, pick...">
                </div>

                <div class="filters">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="pending">Pending</button>
                    <button class="filter-btn" data-filter="won">Won</button>
                    <button class="filter-btn" data-filter="lost">Lost</button>
                </div>
            </section>

            <main class="content">
                <section id="todayPanel" class="tab-panel active">
                    {today_html}
                </section>

                <section id="yesterdayPanel" class="tab-panel">
                    {yesterday_html}
                </section>

                <section id="historyPanel" class="tab-panel">
                    {history_html}
                </section>

                <div id="emptyState" class="empty-state">
                    No matches found for your search or filter.
                </div>

                <div class="bottom-pad"></div>
            </main>
        </div>

        <script>
            const searchInput = document.getElementById("searchInput");
            const filterButtons = document.querySelectorAll(".filter-btn");
            const navTabs = document.querySelectorAll(".nav-tab");
            const tabPanels = document.querySelectorAll(".tab-panel");
            const emptyState = document.getElementById("emptyState");

            let activeFilter = "all";
            let activeTab = "todayPanel";

            function applyFilters() {{
                const query = searchInput.value.trim().toLowerCase();

                tabPanels.forEach(panel => {{
                    const cards = panel.querySelectorAll(".match-card");

                    cards.forEach(card => {{
                        const status = card.dataset.status;
                        const match = card.dataset.match;
                        const league = card.dataset.league;
                        const prediction = card.dataset.prediction;

                        const passesFilter = activeFilter === "all" || status === activeFilter;
                        const passesSearch =
                            match.includes(query) ||
                            league.includes(query) ||
                            prediction.includes(query);

                        const visible = passesFilter && passesSearch;
                        card.style.display = visible ? "" : "none";
                    }});

                    const sections = panel.querySelectorAll(".day-section");
                    sections.forEach(section => {{
                        const cardsInSection = section.querySelectorAll(".match-card");
                        let hasVisible = false;
                        cardsInSection.forEach(card => {{
                            if (card.style.display !== "none") hasVisible = true;
                        }});
                        section.style.display = hasVisible ? "" : "none";
                    }});
                }});

                const activePanel = document.getElementById(activeTab);
                const activeCards = activePanel ? activePanel.querySelectorAll(".match-card") : [];
                let visibleCount = 0;
                activeCards.forEach(card => {{
                    if (card.style.display !== "none") visibleCount += 1;
                }});

                emptyState.style.display = visibleCount === 0 ? "block" : "none";
                window.scrollTo({{ top: 0, behavior: "smooth" }});
            }}

            navTabs.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    navTabs.forEach(b => b.classList.remove("active"));
                    tabPanels.forEach(p => p.classList.remove("active"));

                    btn.classList.add("active");
                    activeTab = btn.dataset.tab;
                    document.getElementById(activeTab).classList.add("active");

                    applyFilters();
                }});
            }});

            filterButtons.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    filterButtons.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    activeFilter = btn.dataset.filter;
                    applyFilters();
                }});
            }});

            searchInput.addEventListener("input", applyFilters);
            applyFilters();
        </script>
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
    html_file = "index.html"
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
                print(f"\\n--- TODAY'S MATCHES ({latest_date}) ---")

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
                match_db[unique_id]["odds"] = odds
                match_db[unique_id]["prediction"] = prediction
                match_db[unique_id]["league"] = league
                match_db[unique_id]["time"] = match_time

            if current_date == latest_date:
                print(f"⚽ {match_name} | Pick: {prediction} | Odds: {odds} | Status: {status}")

    all_matches = list(match_db.values())
    all_matches.sort(
        key=lambda item: time.strptime(item["date"], "%d/%m/%y") if item.get("date") else time.gmtime(0),
        reverse=True
    )

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=4, ensure_ascii=False)

    save_html(all_matches, html_file)

    print("-" * 50)
    print(f"✅ DB Saved to: {json_file}")
    print(f"✅ HTML Saved to: {html_file}")
    print(f"📊 Stats: {new_matches_count} New added | {updated_matches_count} Updated | {len(match_db)} Total in DB")


if __name__ == "__main__":
    scrape_vip_matches()