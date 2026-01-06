# %%
import requests 
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# %%
BASE_URL = "https://movil.asisscad.cl"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Origin": BASE_URL,
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    # 'Accept-Language': 'es-419,es;q=0.5',
    # 'Cache-Control': 'no-cache',
    # 'Pragma': 'no-cache',
    # 'Upgrade-Insecure-Requests': '1'
}

# %%
def extract_form_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        raise ValueError("No form found in the HTML.")
    
    form_data = {}
    for input_tag in form.find_all('input'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    return form_data, form.get('action', ''), form.get('method', 'GET').upper()

# %%
def get_page_form_data(client, url, method="GET", data=None, log=False):
    response = client.request(method, url, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve page: {response.status_code}")

    return extract_form_data(response.text)

# %%
session = requests.Session()
session.headers.update(HEADERS)

# %%
login_response = session.get(BASE_URL)

# %%
login_data, login_ext_url, login_method = extract_form_data(login_response.text)
login_data["txt_id_empresa"] = 7040
login_data["txt_id_usuario"] = 77668171
login_data["txt_pass"] = "Milagros1234"
login_data["__EVENTTARGET"] = "lnk_ingreso"

# %%
login_data

# %%
log_response = session.request(login_method, urljoin(BASE_URL, login_ext_url), data=login_data)

# %%
geo_data, geo_ext_url, geo_method = extract_form_data(log_response.text)
lat = -6.7711
lng = -79.8431

geo_data["txt_lat"] = lat
geo_data["txt_lon"] = lng
geo_data["hf_lat"] = lat
geo_data["hf_lon"] = lng
geo_data["__EVENTTARGET"] = "lnk_proceso"

# %%
geo_data

# %%
assist_response = session.request(geo_method, urljoin(BASE_URL, geo_ext_url), data=geo_data)

# %%
assist_data, assist_ext_url, assist_method = extract_form_data(assist_response.text)

# %%
assist_data

# %%
# Mark the assist_data for the next step
assist_data["__EVENTTARGET"] = "lnk_entrada"

# %%
last_response = session.request(assist_method, urljoin(BASE_URL, assist_ext_url), data=assist_data)
last_data, last_ext_url, last_method = extract_form_data(last_response.text)

# %%
print(BeautifulSoup(last_response.text, 'html.parser').prettify())

# %%
# Mark the assist_data for the next step
# assist_data["__EVENTTARGET"] = "lnk_salida"

# %%
# assist_data["__EVENTTARGET"] = None


