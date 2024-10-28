import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urljoin
import json
import re
from datetime import datetime
from pytz import timezone
import wikipediaapi
import pandas as pd

from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta

## common fetcher
def fetch_and_parse(url, use_session=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    if use_session:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.headers.update(headers)
        requester = session
    else:
        requester = requests
    
    try:
        print(f"Crawling: {url}")
        response = requester.get(url, headers=headers if not use_session else None)
        response.raise_for_status()  # Raise an exception for failed requests
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  
    return None

def create_file_name(url):
    special_chars = r'[:?,&=#%]'
    sanitized_url = re.sub(special_chars, '_', url)
    return sanitized_url.replace('/', '_').strip('_') + ".txt"

def save_page_content(url, soup, output_dir="crawled_pages"):
    page_title = soup.title.string if soup.title and soup.title.string else 'No Title'
    filename = create_file_name(url)
    filename = create_file_name(url)

    os.makedirs(output_dir, exist_ok=True)

    page_content = soup.get_text(separator='\n', strip=True)  # Use newlines between sections

    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as file:
        file.write(page_title + "\n\n")  # Write title followed by a blank line
        file.write(page_content)  # Write main content with newlines between sections
    
    print(f"Saved: {filename}")

# Return all internal links on the page
def extract_links(soup, parsed_base_url):
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        base_url = parsed_base_url.geturl()
        if not base_url.endswith('/'):
            base_url += '/'
        full_url = urljoin(parsed_base_url.geturl(), href)
        parsed_url = urlparse(full_url)
    
        if parsed_url.netloc == parsed_base_url.netloc and parsed_url.path.startswith(parsed_base_url.path):
            links.append(full_url)
    return links

# Main recursive crawl function
def crawl_website(start_url, max_pages=200, output_dir="crawled_pages", recurse=True):
    visited_urls = set()
    urls_to_visit = [start_url]
    parsed_start_url = urlparse(start_url)
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"}

    while urls_to_visit and len(visited_urls) < max_pages:
        current_url = urls_to_visit.pop(0)
        
        if current_url in visited_urls:
            continue
        
        soup = fetch_and_parse(current_url)
        
        if soup:
            save_page_content(current_url, soup, output_dir=output_dir)
            visited_urls.add(current_url)
            
            # Extract new links only if recursion is enabled
            if recurse:
                new_links = extract_links(soup, parsed_start_url)
                print(f"Found {len(new_links)} new links from {current_url}")
                for link in new_links:
                    if (not any(link.lower().endswith(ext) for ext in image_extensions)) and ("pdf" not in link.lower()):
                        if link not in visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)


def crawl_event_pittsburgh(soup: BeautifulSoup, output_filename: str, output_dir="crawled_pages"):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as output_file:
        scripts = soup.find_all('script', type='application/ld+json')

        for script in scripts:
            try:
                json_data = json.loads(script.string)

                if "@type" in json_data and "Event" in json_data["@type"]:
                    json.dump(json_data, output_file, indent=4)
                    output_file.write('\n\n')  
            except json.JSONDecodeError:
                pass  



def crawl_event_info_downtown_pittsburgh(soup: BeautifulSoup, output_filename: str, output_dir="crawled_pages"):
    event_data = []

    event_divs = soup.find_all('div', class_='eventitem')
    os.makedirs(output_dir, exist_ok=True)

    for event_div in event_divs:
        event_info = {}

        title_tag = event_div.find('h1')
        if title_tag and title_tag.a:
            event_info['title'] = clean_text(title_tag.a.get_text(strip=True))
            event_info['url'] = title_tag.a['href']

        category_tag = event_div.find('div', class_='term')
        if category_tag:
            event_info['category'] = clean_text(category_tag.get_text(strip=True))

        event_date_tag = event_div.find('div', class_='eventdate')
        if event_date_tag:
            event_info['date_time'] = clean_text(event_date_tag.get_text(strip=True))

        description = event_div.get_text(separator=" ", strip=True)
        event_info['description'] = clean_text(description)

        script_tag = event_div.find_next('script', type='application/ld+json')
        if script_tag:
            try:
                json_data = json.loads(script_tag.string)
                event_info['json_data'] = json_data
            except json.JSONDecodeError:
                event_info['json_data'] = None 

        event_data.append(event_info)
    
    with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as output_file:
        json.dump(event_data, output_file, indent=4)
        
    print(f"Event information has been saved to {output_filename}")



def clean_text(text: str) -> str:
    """
    Cleans the text by removing tab characters and excessive whitespace.
    """
    text = text.replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_and_save_pgh(soup: BeautifulSoup, output_filename: str, output_dir="crawled_pages"):
    events = []
    event_items = soup.find_all('li', class_='fdn-pres-item')
    
    os.makedirs(output_dir, exist_ok=True)
    
    for event_item in event_items:
        event_info = {}

        title_tag = event_item.find('p', class_='fdn-teaser-headline')
        if title_tag and title_tag.a:
            event_info['title'] = title_tag.a.get_text(strip=True)
            event_info['event_link'] = title_tag.a['href']

        date_tag = event_item.find('p', class_='fdn-teaser-subheadline')
        if date_tag:
            event_info['date_time'] = date_tag.get_text(strip=True)

        location_tag = event_item.find('p', class_='fdn-event-teaser-location')
        if location_tag and location_tag.a:
            event_info['location_name'] = location_tag.a.get_text(strip=True)
            event_info['location_link'] = location_tag.a['href']

        address_tag = event_item.find('p', class_='fdn-inline-split-list')
        if address_tag:
            event_info['address'] = address_tag.get_text(strip=True)

        price_tag = event_item.find('span', class_='uk-margin-xsmall-top')
        if price_tag:
            event_info['price'] = price_tag.get_text(strip=True)

        category_tag = event_item.find('a', class_='fdn-teaser-tag-link')
        if category_tag:
            event_info['category'] = category_tag.get_text(strip=True)

        description_tag = event_item.find('div', class_='fdn-teaser-description')
        if description_tag:
            event_info['description'] = description_tag.get_text(strip=True)

        events.append(event_info)

    if events:
        with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as output_file:
            json.dump(events, output_file, indent=4)
        print(f"Saved {len(events)} events to {output_filename}")
    return len(events) > 0  


def convert_timestamp(ts, tz="America/Detroit"):
    if ts is None:  
        return "Time not available"
    detroit_tz = timezone(tz)
    dt = datetime.fromtimestamp(ts, detroit_tz)
    return dt.strftime('%B %d, %Y, %I:%M %p')  # Format: "Month Day, Year, HH:MM AM/PM"

def save_cmu_event(event_data, file_name):
    all_events = []  
    
    for date_key, events in event_data.get('events', {}).items():
        for event in events:
            title = event.get("title")
            location = event.get("location")
            start_time = event.get("ts_start")
            end_time = event.get("ts_end")
            is_canceled = event.get("is_canceled", "No")
            repeats = event.get("repeats", "")
            description = event.get("summary", "").replace("<p>", "").replace("</p>", "").strip()

            start_time_formatted = convert_timestamp(start_time)
            end_time_formatted = convert_timestamp(end_time)

            event_details = {
                "Title": title,
                "Date": datetime.strptime(date_key, '%Y%m%d').strftime('%B %d, %Y'),
                "Location": location,
                "Start Time": start_time_formatted,
                "End Time": end_time_formatted,
                "Is Canceled": is_canceled,
                "Repeats": repeats,
                "Description": description
            }
            
            all_events.append(event_details)

    with open(file_name, 'w') as file:
        json.dump(all_events, file, indent=4)

def crawl_cmu_events(base_url, output_dir="crawled_pages"):
    page = 1
    max_pages = 1000  # Assume there's a reasonable upper bound
    while page <= max_pages:
        print(f"Crawling page {page}.")
        url = f"{base_url}&page={page}"
        jsondata = fetch(url) 
        if jsondata and 'events' in jsondata and jsondata['events']:
            file_name = os.path.join(output_dir, f"cmu_events_page_{page}.txt")
            save_cmu_event(jsondata, file_name)
            page += 1
        else:
            print(f"Stopping crawl, no events found on page {page}.")
            break


def crawl_wikipedia(url, output_dir="crawled_pages"):
    user_agent = 'MyRAGSystem/1.0 (annanyac@andrew.cmu.edu)'
    wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent=user_agent)
    title = url.split('/')[-1]
    filename = create_file_name(url)
    page = wiki_wiki.page(title)
    os.makedirs(output_dir, exist_ok=True)
    if page.exists():
        print(f"Fetching content from: {page.title}")
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as file:
            file.write(page.text)
        print(f"Text from {title} has been written to {filename}")
    else:
        print(f"Page '{title}' does not exist.")


def crawl_pgh_events(output_dir="crawled_pages"):
    base_url = "https://www.pghcitypaper.com/pittsburgh/EventSearch?narrowByDate=2024-10-26-to-2025-11-20&page={page}&sortType=date&v=d"
    page = 1
    while True:
        url = base_url.format(page=page)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        output_filename = f"events_page_{page}.json"
        
        if not parse_and_save_pgh(soup, output_filename, output_dir):
            print(f"No events found on page {page}. Stopping.")
            break
        
        print(f"Saved pgh events from page {page}.")
        page += 1  # Move to the next page


def crawl_penguin_schedule(api_url, output_dir="schedules", output_file="penguins_schedule.json"):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        schedule = []
        for game in data.get("games", []):
            game_info = {
                "date": game.get("gameDate"),
                "home_team": game.get("homeTeam", {}).get("placeName", {}).get("default", "N/A"),
                "away_team": game.get("awayTeam", {}).get("placeName", {}).get("default", "N/A"),
                "location": game.get("venue", {}).get("default", "Unknown Location")
            }
            schedule.append(game_info)

        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            header_message = {
                "note": "The below is the schedule of the Pittsburgh Penguins for the 2024-2025 season",
                "schedule": schedule
            }
            json.dump(header_message, f, indent=4)
        
        print(f"Schedule data saved to {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")



def crawl_pirates_schedule(output_file="pirates_schedule_summary.json", output_dir="schedules"):
    os.makedirs(output_dir, exist_ok=True)
    
    start_date = datetime.strptime("2025-03-01", "%Y-%m-%d")
    end_date = datetime.strptime("2025-09-30", "%Y-%m-%d")
    current_date = start_date
    
    schedule_data = {
        "header": "Pittsburgh Pirates Schedule for the 2025 Season",
        "games": []
    }
    
    while current_date <= end_date:
        next_date = min(current_date + timedelta(days=45), end_date)
        
        api_url = f"https://statsapi.mlb.com/api/v1/schedule?lang=en&sportIds=1,51,21&hydrate=team(venue(timezone)),venue(timezone),game(seriesStatus,seriesSummary,tickets,promotions,sponsorships,content(summary,media(epg))),seriesStatus,seriesSummary,broadcasts(all),linescore,tickets,event(tickets,game,sport,league,status,xref),radioBroadcasts&season=2025&startDate={current_date.strftime('%Y-%m-%d')}&endDate={next_date.strftime('%Y-%m-%d')}&teamId=134,373&timeZone=America/New_York&eventTypes=primary&scheduleTypes=games,events,xref"
        
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            for date_info in data.get("dates", []):
                game_date = date_info.get("date")
                for game in date_info.get("games", []):
                    game_info = {
                        "date": game_date,
                        "location": game.get("venue", {}).get("name"),
                        "home_team": game.get("teams", {}).get("home", {}).get("team", {}).get("name"),
                        "away_team": game.get("teams", {}).get("away", {}).get("team", {}).get("name")
                    }
                    schedule_data["games"].append(game_info)
        else:
            print(f"Failed to fetch data for range {current_date} to {next_date}. Status code: {response.status_code}")
        
        current_date = next_date + timedelta(days=1)

    output_path = os.path.join(output_dir, output_file)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(schedule_data, file, indent=4)
    
    print(f"Parsed schedule saved to {output_path}")


def download_pdf(url, output_folder):
    filename = os.path.join(output_folder, url.split('/')[-1])
    
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()  # Check if the request was successful
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"Downloaded: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

crawl_cmu_events("https://events.cmu.edu/live/calendar/view/all?user_tz=America%2FDetroit&template_vars=id,latitude,longitude,location,time,href,image_raw,title_link,summary,until,is_canceled,is_online,image_src,repeats,is_multi_day,is_first_multi_day,multi_day_span,tag_classes,category_classes,has_map&syntax=%3Cwidget%20type%3D%22events_calendar%22%3E%3Carg%20id%3D%22mini_cal_heat_map%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22thumb_width%22%3E200%3C%2Farg%3E%3Carg%20id%3D%22thumb_height%22%3E200%3C%2Farg%3E%3Carg%20id%3D%22hide_repeats%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22show_groups%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22show_locations%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22show_tags%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22month_view_day_limit%22%3E2%3C%2Farg%3E%3Carg%20id%3D%22use_tag_classes%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22search_all_events_only%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22use_modular_templates%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22exclude_tag%22%3Eexclude%20from%20main%20calendar%3C%2Farg%3E%3Carg%20id%3D%22display_all_day_events_last%22%3Etrue%3C%2Farg%3E%3C%2Fwidget%3E", output_dir="scraped_data/cmu_events")
crawl_website("https://www.cmu.edu/engage/alumni/events/campus/",output_dir="scraped_data/crawled_pages")
crawl_pgh_events(output_dir="scraped_data/crawled_pages")
file_path = './general_urls.csv'
df = pd.read_csv(file_path)

for url in df.iloc[:, 0]:  # Access the first column
    if 'en.wikipedia.org' in url:
        crawl_wikipedia(url, output_dir="scraped_data/crawled_pages")
    elif 'pittsburgh.events' in url:
        crawl_event_pittsburgh(fetch_and_parse(url), create_file_name(url), output_dir="scraped_data/crawled_pages")
    elif 'downtownpittsburgh.com' in url:
        crawl_event_info_downtown_pittsburgh(fetch_and_parse(url), create_file_name(url), output_dir="scraped_data/crawled_pages")

# crawl_website("https://bananasplitfest.com/", output_dir="banana_split_fest")
crawl_website("https://littleitalydays.com/", output_dir="scraped_data/little_italy_days")
crawl_website("https://pittsburghrestaurantweek.com/", output_dir="scraped_data/pittburgh_restaurant_week")
crawl_website("https://www.pghtacofest.com/", output_dir="scraped_data/pgh_taco_fest")
crawl_website("https://www.picklesburgh.com/", output_dir="scraped_data/pickles_burgh")



crawl_website("https://www.visitpittsburgh.com/events-festivals/food-festivals/", output_dir="scraped_data/food_festivals")
crawl_website("https://carnegiemuseums.org/", output_dir="scraped_data/museum")
crawl_website("https://www.heinzhistorycenter.org/", output_dir="scraped_data/museum")
crawl_website("https://www.thefrickpittsburgh.org/", output_dir="scraped_data/museum")

crawl_website("https://www.pittsburghsymphony.org/", output_dir="scraped_data/arts")
crawl_website("https://pittsburghopera.org/", output_dir="scraped_data/arts")
crawl_website("https://trustarts.org/", output_dir="scraped_data/arts")
crawl_website("https://www.visitpittsburgh.com/things-to-do/pittsburgh-sports-teams/", output_dir="scraped_data/sports")
crawl_penguin_schedule("https://api-web.nhle.com/v1/club-schedule-season/pit/20242025", output_dir="scraped_data/schedules")
crawl_pirates_schedule(output_dir="scraped_data/schedules")
crawl_website("https://www.steelers.com/schedule/index", output_dir="scraped_data/schedules")
crawl_website("http://www.cmu.edu/leadership/", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/mission.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/history.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/traditions.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("http://www.cmu.edu/diversity", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/pittsburgh.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/rankings.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.cmu.edu/about/awards.html", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.britannica.com/place/Pittsburgh", output_dir="scraped_data/general_info", recurse=False)
crawl_website("https://www.visitpittsburgh.com/", output_dir="scraped_data/visit pittsburgh")
crawl_website("https://www.pittsburghpa.gov/Home", output_dir="scraped_data/pittsburgh_gov")


csv_file_path = 'pdf_urls.csv'
output_folder = 'scraped_data/pdfs'
urls = pd.read_csv(csv_file_path, header=None).squeeze().tolist()
for url in urls:
    download_pdf(url, output_folder)
