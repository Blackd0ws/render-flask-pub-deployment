from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import xml.etree.ElementTree as ET
import requests
from flask import Flask, render_template_string
import pandas as pd


#Pour changer les paramètres dans une url
def replace_url_param(url, param_name, new_value):
    """Remplace un paramètre spécifique d'une URL par une nouvelle valeur et conserve les champs vides."""
    
    # Analyser l'URL
    parsed_url = urlparse(url)
    
    # Extraire les paramètres de requête sous forme de dictionnaire
    query_params = parse_qs(parsed_url.query)
    
    # Remplacer ou ajouter le paramètre
    query_params[param_name] = [new_value]  # Remplacer ou ajouter
    
    # S'assurer que les champs vides sont présents
    all_params = ['site_id', 'app_bundle', 'did', 'format', 'cb', 'ua', 'player_height', 'player_width', 'app_category', 
                  'app_domain', 'app_name', 'app_store_url', 'app_version', 'consent', 'livestream', 'position', 'device_type', 
                  'gdpr', 'max_ad_duration', 'min_ad_duration', 'pod_duration', 'slot_count', 'content_channel', 'content_context', 
                  'content_genre', 'content_id', 'content_language', 'content_length', 'content_prodqual', 'content_series', 
                  'content_title', 'content_keywords', 'custom_10', 'custom_11', 'custom_12', 'custom_13', 'custom_14', 
                  'custom_15', 'custom_16', 'custom_17', 'custom_18', 'custom_5', 'custom_6', 'custom_7', 'custom_8', 'custom_9']
    
    # Ajouter les paramètres vides manquants
    for param in all_params:
        if param not in query_params:
            query_params[param] = ['']
    
    # Reconstruire la chaîne de requête avec tous les paramètres
    query_string = urlencode(query_params, doseq=True)
    
    # Reconstruire l'URL avec les nouveaux paramètres
    new_url = parsed_url._replace(query=query_string)
    
    # Retourner l'URL modifiée sous forme de chaîne
    return urlunparse(new_url)

#Pour tester le flux de pub
def test_pub(url):
    # Récupérer le contenu XML
    response = requests.get(url, timeout=5)
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type')
        if 'xml' in content_type:
            try:
                # Parser le XML
                root = ET.fromstring(response.content)
                
                # Vérifier si la racine du XML contient seulement la balise <VAST version="3.0" />
                if root.tag == "VAST" and root.attrib.get('version') == "3.0" and len(root) == 0:
                    return False  # Renvoie False si c'est seulement <VAST version="3.0" />
                else:
                    return True  # Renvoie True si le contenu du XML est plus complexe
            except ET.ParseError:
                print("Erreur de parsing XML")
                return False
        else:
            print("Le contenu de la réponse n'est pas du XML")
            return False
    else:
        print(f"Erreur lors de la récupération du fichier XML : {response.status_code}")
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
#Liste des types de vidéos
videos = ['LACHAINE', 'VOD']
#videos = ['LACHAINE', 'VOD']
#Liste des versions
versions = ['prod', 'preprod', 'uat']
#Liste des pubs
type_pub = ['simple', 'tunnel']
pubs = ['', 60]
#Liste des positions
noMid = ['preroll']
Mid = ['preroll', 'midroll']

#Plateformes:
#plateformes = ["Samsung", "LG", "Orange", "Bouygues", "Google"]
plateformes = ["Samsung", "LG", "Google"]
#Samsung puis LG puis Orange puis Bouygues puis Google
#id_lives = ["47370", "47784", "47785", "47788", "48269"]
id_lives = ["47370", "47784", "48269"]
#id_vod = ["47782", "47783", "47787", "47789", "48270"]
id_vod = ["47782", "47783", "48270"]


app = Flask(__name__)

@app.route('/')
#On passe à la construction du tableau ainsi qu'à la réalisation des tests
def tableau():
    #On va rentrer l'url qui contient un flux quelconque de pub
    url = 'https://pbs-eu.getpublica.com/v1/s2s-hb?site_id=47370&app_bundle=lequipe&did=m7xc13m0-hn&format=vast&cb=1741265381087&ua=Mozilla%252F5.0%2520(Web0S%253B%2520Linux%252FSmartTV)%2520AppleWebKit%252F537.36%2520(KHTML%252C%2520like%2520Gecko)%2520Chrome%252F79.0.3945.79%2520Safari%252F537.36%2520WebAppManageR&player_height=1080&player_width=1920&app_category=&app_domain=lequipe.fr&app_name=lequipe&app_store_url=&app_version=1.2.1&consent=CQN2PcAQN2PcAAHABBENBfFgAAAAAAAAAAAAAAAAAAAA.YAAAAAAAAAAA&livestream=1&position=preroll&device_type=CONNECTED%2520TV&gdpr=1&max_ad_duration=60&min_ad_duration=1&pod_duration=&slot_count=&content_channel=lequipe&content_context=1&content_genre=sport&content_id=k5s40USR9HxnG5aCf1y&content_language=fr&content_length=&content_prodqual=1&content_series=&content_title=la-chaine&content_keywords=lequipe-21%252Ctous-sports%252Cbande-annonce%252Clequipe-du-soir%252Ceds%252Colivier-menard%252Cdebat%252Canalyse%252Chumour%252Cbundes&custom_10=&custom_11=&custom_12=&custom_13=&custom_14=&custom_15=&custom_16=&custom_17=&custom_18=prod&custom_5=&custom_6=LACHAINE&custom_7=&custom_8=&custom_9='

    # Nos colonnes et index
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
        ('AndroidTV', 'prod'), ('AndroidTV', 'preprod'), ('AndroidTV', 'uat')
    ])
    index = [
        'live - preroll simple', 'live - preroll multi',
        'VOD - preroll simple', 'VOD - preroll multi',
        'VOD - midroll simple' , 'VOD - midroll multi'
    ]
    data = []

    #On passe à nos tests pour pouvoir construire la dataframe
    for a in videos:
        url = replace_url_param(url, 'custom_6', a)
        #On passe à la position
        for position in isMidroll(a):
            url = replace_url_param(url, 'position', position)
            #On passe au type de pub:
            for c in pubs:
                datas = []
                url = replace_url_param(url, 'pod_duration', c)
                #On passe aux plateformes
                for i in whichId(a):
                    url = replace_url_param(url, "site_id", i)
                    #On passe à la version
                    for b in versions:
                        url = replace_url_param(url, 'custom_18', b)
                        if test_pub(url):
                            donnee = f'<a href="{url}">url</a> ✅'
                        else:
                            donnee = f'<a href="{url}">url</a> ❌'
                        datas.append(donnee)
                data.append(datas)

    #On assemble la dataframe
    df = pd.DataFrame(data=data, index=index, columns=colonnes)

    # Convertir la DataFrame en HTML, en autorisant les balises HTML
    tableau_html = df.to_html(escape=False, index=True)

    # Afficher le tableau dans une page simple
    html_template = f"""
    <html>
        <head>
            <title>Tests sur les pubs</title>
        </head>
        <body>
            {tableau_html}
        </body>
    </html>
    """

    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(debug=True)