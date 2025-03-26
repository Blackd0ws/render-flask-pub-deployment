<?php
// filepath: /opt/lampp/htdocs/tests/TestsPubs/PubAuto.php

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

require __DIR__ . '/../vendor/autoload.php';

// Pour changer les paramètres dans une URL
function replace_url_param($url, $param_name, $new_value) {
    $parsed_url = parse_url($url);
    parse_str($parsed_url['query'], $query_params);
    $query_params[$param_name] = $new_value;
    $query_string = http_build_query($query_params);
    $new_url = $parsed_url['scheme'] . '://' . $parsed_url['host'] . $parsed_url['path'] . '?' . $query_string;
    return $new_url;
}

// Liste pour stocker les messages d'erreur
$error_logs = [];

// Fonction pour extraire les URLs contenues dans les CDATA des balises MediaFiles du XML
function extract_cdata_urls_from_mediafiles($root) {
    $urls = [];
    if (isset($root->MediaFiles) && $root->MediaFiles !== null) {
        foreach ($root->MediaFiles as $mediafiles) {
            foreach ($mediafiles as $elem) {
                if (strpos($elem, "http") !== false) {
                    $urls[] = trim($elem);
                }
            }
        }
    }
    return $urls;
}

function position($x, $y): string {
    $yi = ["Samsung-prod", "Samsung-preprod", "Samsung-uat", "LG-prod", "LG-preprod", "LG-uat", "Bouygues-prod", "Bouygues-preprod", "Bouygues-uat", "AndroidTV-prod", "AndroidTV-preprod", "AndroidTV-uat"];
    $xi = ["live - preroll simple", "live - preroll multi", "VOD - preroll simple", "VOD - preroll multi", "VOD - midroll simple", "VOD - midroll multi"];
    return $xi[$x] . ", " . $yi[$y] . " : ";
}

function check_cdata_url($cdata_url, $x, $y) {
    global $error_logs;
    if (!str_ends_with($cdata_url, ".mp4")) {
        $error_logs[] = position($x, $y) . "URL CDATA ne se termine pas par .mp4 ($cdata_url)";
        return false;
    }
    try {
        $client = new Client();
        $response = $client->get($cdata_url, ['timeout' => 30]); // Augmenter le délai d'attente à 30 secondes
        if ($response->getStatusCode() != 200) {
            $error_logs[] = position($x, $y) . "URL CDATA inaccessible ($cdata_url)";
            return false;
        }
    } catch (RequestException $e) {
        $error_logs[] = position($x, $y) . "Erreur lors de l'accès à l'URL CDATA ($cdata_url): " . $e->getMessage();
        return false;
    }
    return true;
}

// Pour tester le flux de pub
function test_pub($url, $n, $x, $y): array {
    global $error_logs;
    try {
        $client = new Client();
        $response = $client->get($url, ['timeout' => 30]); // Augmenter le délai d'attente à 30 secondes
        if ($response->getStatusCode() == 200) {
            $content_type = $response->getHeaderLine('Content-Type');
            if (strpos($content_type, 'xml') !== false) {
                $root = new SimpleXMLElement($response->getBody()->getContents());
                if ($root->getName() == "VAST" && $root['version'] == "3.0" && count($root->children()) == 0) {
                    return [false, true];
                } else {
                    $urls = extract_cdata_urls_from_mediafiles($root);
                    $results = array_map(function($u) use ($x, $y) {
                        return [check_cdata_url($u, $x, $y), false];
                    }, $urls);
                    if (!in_array(false, $results)) {
                        $xml_text = $root->asXML();
                        $count = substr_count(strtolower($xml_text), "duration") / 2;
                        if (($count == 1 && $n == 1) || ($count > 1 && $n == 2)) {
                            return [true, false];
                        }
                        $error_logs[] = position($x, $y) . "Nombre de pubs incorrect ($count)";
                        return [false, false];
                    }
                    return [false, false];
                }
            } else {
                $error_logs[] = position($x, $y) . "Le contenu de la réponse n'est pas du XML pour l'URL: $url";
                return [false, false];
            }
        } else {
            $error_logs[] = position($x, $y) . "Erreur lors de la récupération du fichier XML : " . $response->getStatusCode() . " pour l'URL: $url";
            return [false, false];
        }
    } catch (RequestException $e) {
        $error_logs[] = position($x, $y) . "Erreur lors de la récupération du fichier XML : " . $e->getMessage() . " pour l'URL: $url";
        return [false, false];
    }
}

// Pour déterminer les IDs à utiliser
function whichId($type_video) {
    global $id_lives, $id_vod;
    if (($type_video == "LACHAINE") || ($type_video == "LIVE-1")) {
        return $id_lives;
    }
    return $id_vod;
}

// Parce que pour les VODs on a aussi la midroll:
function isMidroll($type_video) {
    global $Mid, $noMid;
    if ($type_video == 'VOD') {
        return $Mid;
    }
    return $noMid;
}

function change_n($k): int {
    if ($k == 1) {
        return 2;
    }
    return 1;
}

// Les données principales:
$videos = ['LACHAINE', 'VOD'];
$versions = ['prod', 'preprod', 'uat'];
$param_pub = [1, 2];
$pubs = ['', 60];
$noMid = ['preroll'];
$Mid = ['preroll', 'midroll'];
$plateformes = ["Samsung", "LG", "Bouygues", "Google"];
$id_lives = [47370, 47784, 47788, 48269];
$id_vod = [47782, 47783, 47789, 48270];

$ligne = 0;
$colonne = 0;
$url = 'https://pbs-eu.getpublica.com/v1/s2s-hb?site_id=47370&app_bundle=lequipe&did=m8q2vns3-ib&format=vast&cb=1743002874960&ua=Mozilla%252F5.0%2520(SMART-TV%253B%2520Linux%252FSmartTV)%2520AppleWebKit%252F537.36%2520(KHTML%252C%2520like%2520Gecko)%2520Chrome%252F79.0.3945.79%2520Safari%252F537.36%2520WebAppManager&player_height=1080&player_width=1920&app_category=&app_domain=ctv.lequipe.eu&app_name=lequipe&app_store_url=&app_version=1.2.2&consent=CQO4KMAQO4KMAAHABBENBiFoAPIAAELAAAAAGuQAgF5gNcAvOACAvMAA.fkAACFgAAAAA&livestream=1&position=preroll&device_type=CONNECTED%2520TV&gdpr=1&max_ad_duration=60&min_ad_duration=1&pod_duration=60&slot_count=&content_channel=lequipe&content_context=1&content_genre=sport&content_id=k1kypsRZF9plQhqwBRS&content_language=fr&content_length=&content_prodqual=1&content_series=&content_title=live-1&content_keywords=equipe%252Cevent&custom_10=&custom_11=&custom_12=&custom_13=&custom_14=&custom_15=&custom_16=&custom_17=&custom_18=uat&custom_5=&custom_6=LIVE-1&custom_7=&custom_8=&custom_9=';
$colonnes = [
    ['Samsung', 'prod'], ['Samsung', 'preprod'], ['Samsung', 'uat'],
    ['LG', 'prod'], ['LG', 'preprod'], ['LG', 'uat'],
    ['Bouygues', 'prod'], ['Bouygues', 'preprod'], ['Bouygues', 'uat'],
    ['AndroidTV', 'prod'], ['AndroidTV', 'preprod'], ['AndroidTV', 'uat']
];

$index = [
    'live - preroll simple', 'live - preroll multi',
    'VOD - preroll simple', 'VOD - preroll multi',
    'VOD - midroll simple', 'VOD - midroll multi'
];

$data = [];
$n = 1;

foreach ($videos as $a) {
    $url = replace_url_param($url, 'custom_6', $a);
    foreach (isMidroll($a) as $position) {
        $url = replace_url_param($url, 'position', $position);
        foreach ($pubs as $c) {
            $datas = [];
            $url = replace_url_param($url, 'pod_duration', $c);
            if($a != 'VOD')
                if ($c === 60){
                    $ae = "LIVE-1";
                    $url = replace_url_param($url, 'custom_6', $ae);
                }else{
                    $ae = 'LACHAINE';
                    $url = replace_url_param($url, 'custom_6', $ae);
                }
            foreach (whichId($a) as $i) {
                $url = replace_url_param($url, "site_id", $i);
                foreach ($versions as $b) {
                    $url = replace_url_param($url, 'custom_18', $b);
                    $test_result = test_pub($url, $n, $ligne, $colonne);
                    if ($test_result[0]) {
                        $donnee = "<a href=\"$url\">url</a> ✅";
                    } else {
                        $donnee = "<a href=\"$url\">url</a> ❌";
                    }
                    $highlight_class = $test_result[1] ? "highlight" : "";
                    $datas[] = "<td class=\"$highlight_class\">$donnee</td>";
                    $colonne++;
                }
            }
            $ligne++;
            $colonne = 0;
            $data[] = $datas;
            $n = change_n($n);
        }
    }
}

// Génération du tableau HTML
$tableau_html = "<table border='1'>";
$tableau_html .= "<thead><tr><th></th>";
foreach ($colonnes as $col) {
    $tableau_html .= "<th>{$col[0]} - {$col[1]}</th>";
}
$tableau_html .= "</tr></thead><tbody>";
foreach ($data as $i => $row) {
    $tableau_html .= "<tr><td>{$index[$i]}</td>";
    foreach ($row as $cell) {
        $tableau_html .= $cell;
    }
    $tableau_html .= "</tr>";
}
$tableau_html .= "</tbody></table>";

// Génération des logs d'erreurs HTML
$error_logs_html = implode("<br>", $error_logs);

// Template HTML final
$html_template = <<<HTML
<html>
    <head>
        <title>Tests sur les pubs</title>
        <style>
            .highlight {
                border: 2px solid red;
                background-color: yellow;
            }
        </style>
    </head>
    <body>
        $tableau_html
        <h2>Logs des erreurs</h2>
        <div>$error_logs_html</div>
    </body>
</html>
HTML;

echo $html_template;
?>
