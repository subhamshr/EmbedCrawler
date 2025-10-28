from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def crawl_headings_with_text(base_url, max_depth=2, max_pages=5):
    visited = set()
    to_visit = [(base_url, 0)]
    data = []
    base_domain = urlparse(base_url).netloc

    while to_visit and len(visited) < max_pages:
        url, depth = to_visit.pop(0)
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup.find_all(['h1', 'h2', 'h3']):
            heading_text = tag.get_text(strip=True)

            link_tag = tag.find('a', href=True)
            if link_tag:
                heading_url = urljoin(url, link_tag['href'])
            else:
                heading_id = tag.get('id')
                heading_url = f"{url}#{heading_id}" if heading_id else url
            section_text = []
            for sibling in tag.find_next_siblings():
                if sibling.name and sibling.name in ['h1', 'h2', 'h3']:
                    break
                if sibling.name == 'p':
                    section_text.append(sibling.get_text(strip=True))
            section_text = " ".join(section_text)

            entry = {
                "heading": heading_text,
                "url": heading_url,
                "text": section_text,
                "longest_paragraph": ''
            }
            if link_tag:
                try:
                    sub_resp = requests.get(heading_url, timeout=10)
                    sub_resp.raise_for_status()
                    sub_soup = BeautifulSoup(sub_resp.text, "html.parser")

                    paragraphs = [p.get_text(strip=True) for p in sub_soup.find_all("p")]
                    if paragraphs:
                        longest_p = max(paragraphs, key=len)
                        entry["longest_paragraph"] = longest_p
                except requests.RequestException as e:
                    print(f"Could not fetch")

            data.append(entry)

        for a in soup.find_all('a', href=True):
            link = urljoin(url, a['href'])
            if base_domain in urlparse(link).netloc and link not in visited:
                to_visit.append((link, depth + 1))

        print(f"Visited {len(visited)} pages so far")

    return data
