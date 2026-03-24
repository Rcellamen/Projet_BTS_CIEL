import requests


def envoi_requete(ip, port=80, endpoint="/", valeur=None):
    """
    Envoie une requête HTTP au serveur.

    Si `valeur` est None, effectue un GET.
    Sinon, effectue un POST avec `valeur` sérialisé en JSON.
    Retourne le texte de la réponse, ou un message d'erreur en cas d'échec.
    """
    try:
        url = f"http://{ip}:{port}{endpoint}"
        if valeur is None:
            return requests.get(url, timeout=5).text
        return requests.post(url, timeout=5, json=valeur).text
    except requests.exceptions.RequestException as e:
        return f"Erreur: {e}"