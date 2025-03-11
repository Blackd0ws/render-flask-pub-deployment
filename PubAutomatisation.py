from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import xml.etree.ElementTree as ET
import requests
from flask import Flask, render_template_string
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os

#Pour changer les paramètres dans une url
def replace_url_param(url, param_name, new_value):
    """Remplace un paramètre spécifique d'une URL par une nouvelle valeur et conserve les champs vides."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params[param_name] = [new_value]
    all_params = ['site_id', 'app_bundle', 'did', 'format', 'cb', 'ua', 'player_height', 'player_width', 'app_category', 
                  'app_domain', 'app_name', 'app_store_url', 'app_version', 'consent', 'livestream', 'position', 'device_type', 
                  'gdpr', 'max_ad_duration', 'min_ad_duration', 'pod_duration', 'slot_count', 'content_channel', 'content_context', 
                  'content_genre', 'content_id', 'content_language', 'content_length', 'content_prodqual', 'content_series', 
                  'content_title', 'content_keywords', 'custom_10', 'custom_11', 'custom_12', 'custom_13', 'custom_14', 
                  'custom_15', 'custom_16', 'custom_17', 'custom_18', 'custom_5', 'custom_6', 'custom_7', 'custom_8', 'custom_9']
    for param in all_params:
        if param not in query_params:
            query_params[param] = ['']
    query_string = urlencode(query_params, doseq=True)
    new_url = parsed_url._replace(query=query_string)
    return urlunparse(new_url)

# Liste pour stocker les messages d'erreur
error_logs = []

#Fonction pour extraire les urls contenues dans les CDATA des balises MediaFiles du XML
def extract_cdata_urls_from_mediafiles(root):
    """Extrait les URLs contenues dans les sections CDATA des balises MediaFiles du XML."""
    urls = []
    for mediafiles in root.iter('MediaFiles'):
        for elem in mediafiles.iter():
            if elem.text and "http" in elem.text:
                urls.append(elem.text.strip())
    return urls

def check_cdata_url(cdata_url, x, y):
    if not cdata_url.endswith(".mp4"):
        error_logs.append(f"Case({x},{y}): URL CDATA ne se termine pas par .mp4 ({cdata_url})")
        return False
    try:
        cdata_response = requests.get(cdata_url, timeout=5)
        if cdata_response.status_code != 200:
            error_logs.append(f"Case({x},{y}): URL CDATA inaccessible ({cdata_url})")
            return False
    except requests.exceptions.RequestException as e:
        error_logs.append(f"Case({x},{y}): Erreur lors de l'accès à l'URL CDATA ({cdata_url}): {e}")
        return False
    return True

#Pour tester le flux de pub
def test_pub(url, n, x, y):
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type')
        if 'xml' in content_type:
            try:
                root = ET.fromstring(response.content)
                if root.tag == "VAST" and root.attrib.get('version') == "3.0" and len(root) == 0:
                    return False
                else:
                    urls = extract_cdata_urls_from_mediafiles(root)
                    with ThreadPoolExecutor() as executor:
                        results = list(executor.map(lambda u: check_cdata_url(u, x, y), urls))
                    if not all(results):
                        return False
                    xml_text = ET.tostring(root, encoding='utf-8').decode()
                    count = xml_text.lower().count("Duration")
                    count /= 2
                    if (count == 1 and n == 1) or (count > 1 and n == 2):
                        return True
                    error_logs.append(f"Case({x},{y}): Nombre de pubs incorrect ({count})")
                    return False
            except ET.ParseError:
                error_logs.append(f"Case({x},{y}): Erreur de parsing XML pour l'URL: {url}")
                return False
        else:
            error_logs.append(f"Case({x},{y}): Le contenu de la réponse n'est pas du XML pour l'URL: {url}")
            return False
    else:
        error_logs.append(f"Case({x},{y}): Erreur lors de la récupération du fichier XML : {response.status_code} pour l'URL: {url}")
        return False

#Pour déterminer les IDs à utiliser
def whichId(type_video):
    if type_video == "LACHAINE":
        return id_lives
    return id_vod

#Parce que pour les VODs on a aussi la midroll:
def isMidroll(type_video):
    if type_video == 'VOD':
        return Mid
    return noMid

#Les données principales:
videos = ['LACHAINE', 'VOD']
versions = ['prod', 'preprod', 'uat']
param_pub = [1, 2]
pubs = ['', 60]
noMid = ['preroll']
Mid = ['preroll', 'midroll']
plateformes = ["Samsung", "LG", "Bouygues", "Google"]
#plateformes = ["Samsung", "LG", "Orange", "Bouygues", "Google"]
id_lives = [47370, 47784, 47788, 48269]
#id_lives = ["47370", "47784", "47785", "47788", "48269"]
id_vod = [47782, 47783, 47789, 48270]
#id_vod = ["47782", "47783", "47787", "47789", "48270"]

app = Flask(__name__)

@app.route('/')
def tableau():
    ligne = 0
    colonne = 0
    url = 'https://pbs-eu.getpublica.com/v1/s2s-hb?site_id=47370&app_bundle=lequipe&did=m7xc13m0-hn&format=vast&cb=1741265381087&ua=Mozilla%252F5.0%2520(Web0S%253B%2520Linux%252FSmartTV)%2520AppleWebKit%252F537.36%2520(KHTML%252C%2520like%2520Gecko)%2520Chrome%252F79.0.3945.79%2520Safari%252F537.36%2520WebAppManageR&player_height=1080&player_width=1920&app_category=&app_domain=lequipe.fr&app_name=lequipe&app_store_url=&app_version=1.2.1&consent=CQN2PcAQN2PcAAHABBENBfFgAAAAAAAAAAAAAAAAAAAA.YAAAAAAAAAAA&livestream=1&position=preroll&device_type=CONNECTED%2520TV&gdpr=1&max_ad_duration=60&min_ad_duration=1&pod_duration=&slot_count=&content_channel=lequipe&content_context=1&content_genre=sport&content_id=k5s40USR9HxnG5aCf1y&content_language=fr&content_length=&content_prodqual=1&content_series=&content_title=la-chaine&content_keywords=lequipe-21%252Ctous-sports%252Cbande-annonce%252Clequipe-du-soir%252Ceds%252Colivier-menard%252Cdebat%252Canalyse%252Chumour%252Cbundes&custom_10=&custom_11=&custom_12=&custom_13=&custom_14=&custom_15=&custom_16=&custom_17=&custom_18=prod&custom_5=&custom_6=LACHAINE&custom_7=&custom_8=&custom_9='
    '''colonnes = pd.MultiIndex.from_tuples([
        ('Samsung', 'prod'), ('Samsung', 'preprod'), ('Samsung', 'uat'),
        ('LG', 'prod'), ('LG', 'preprod'), ('LG', 'uat'),
        ('Orange', 'prod'), ('Orange', 'preprod'), ('Orange', 'uat'),
        ('Bouygues', 'prod'), ('Bouygues', 'preprod'), ('Bouygues', 'uat'),
        ('AndroidTV', 'prod'), ('AndroidTV', 'preprod'), ('AndroidTV', 'uat')
    ])'''
    colonnes = pd.MultiIndex.from_tuples([
        ('Samsung', 'prod'), ('Samsung', 'preprod'), ('Samsung', 'uat'),
        ('LG', 'prod'), ('LG', 'preprod'), ('LG', 'uat'),
        ('Bouygues', 'prod'), ('Bouygues', 'preprod'), ('Bouygues', 'uat'),
        ('AndroidTV', 'prod'), ('AndroidTV', 'preprod'), ('AndroidTV', 'uat')
    ])
    index = [
        'live - preroll simple', 'live - preroll multi',
        'VOD - preroll simple', 'VOD - preroll multi',
        'VOD - midroll simple' , 'VOD - midroll multi'
    ]
    data = []

    for a in videos:
        url = replace_url_param(url, 'custom_6', a)
        for position in isMidroll(a):
            url = replace_url_param(url, 'position', position)
            for c, n in zip(pubs, param_pub):
                datas = []
                url = replace_url_param(url, 'pod_duration', c)
                for i in whichId(a):
                    url = replace_url_param(url, "site_id", i)
                    for b in versions:
                        url = replace_url_param(url, 'custom_18', b)
                        if test_pub(url, n, ligne, colonne):
                            donnee = f'<a href="{url}">url</a> ✅'
                        else:
                            donnee = f'<a href="{url}">url</a> ❌'
                        datas.append(donnee)
                        colonne += 1
                ligne += 1
                colonne = 0
                data.append(datas)

    df = pd.DataFrame(data=data, index=index, columns=colonnes)
    tableau_html = df.to_html(escape=False, index=True)
    error_logs_html = "<br>".join(error_logs)

    html_template = f"""
    <html>
        <head>
            <title>Tests sur les pubs</title>
        </head>
        <body>
            {tableau_html}
            <h2>Logs des erreurs</h2>
            <div>{error_logs_html}</div>
        </body>
    </html>
    """

    return render_template_string(html_template)

'''if __name__ == '__main__':
    app.run(debug=True)'''

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Utilise le port donné par Render ou 5000 par défaut
    app.run(host="0.0.0.0", port=port, debug=True)
