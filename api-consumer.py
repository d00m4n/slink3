import requests
import json

# URL de l'API
api_url = "http://192.168.150.11:5000/api/addlink"

# Dades de l'enllaç a afegir
link_data = {
    "description": "Exemple d'enllaç",
    "url": "https://exemple.com",
    "type_id": 1,
    "icon": "exemple.png"
}

# Capçaleres de la sol·licitud
headers = {
    "Content-Type": "application/json"
}

# Enviar una sol·licitud POST a l'API
response = requests.post(api_url, data=json.dumps(link_data), headers=headers)

# Verificar el codi d'estat de la resposta
if response.status_code == 201:
    print("Enllaç afegit amb èxit!")
else:
    print(f"Error en afegir l'enllaç. Codi d'estat: {response.status_code}")
    print(f"Missatge d'error: {response.text}")