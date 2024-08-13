import requests
import json
import pandas as pd

# Configuración de autenticación
tenant_id = 'ccd33858-8dfe-4420-a02f-1f83e7b28d9d'
client_id = '4f68d916-5f48-45f3-8ab3-5b88b89a1eea'
client_secret = 'ive8Q~lYsM5J1GsGXW5me5oSgn3Ev.T_sbU_Nb_n'

# URLs de Microsoft Graph API
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
graph_url = "https://graph.microsoft.com/v1.0"

# Obtener el token de acceso
def get_access_token():
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    response = requests.post(token_url, data=data, verify=False)
    response.raise_for_status()
    return response.json().get('access_token')

# Crear grupo
def create_group(access_token, group_data):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups"
    response = requests.post(url, headers=headers, json=group_data)
    response.raise_for_status()
    return response.json()

# Crear usuario
def create_user(access_token, user_data):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/users"
    response = requests.post(url, headers=headers, json=user_data)
    
    # Verifica si la respuesta tiene contenido JSON
    if response.status_code == 201:  # 201 Created es esperado al crear un usuario
        try:
            return response.json()
        except json.JSONDecodeError:
            print(f"Advertencia: No se pudo decodificar la respuesta JSON: {response.text}")
            return None
    else:
        response.raise_for_status()

# Añadir usuario a grupo
def add_user_to_group(access_token, user_id, group_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups/{group_id}/members/$ref"
    body = {
        "@odata.id": f"{graph_url}/directoryObjects/{user_id}"
    }
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    
    # Verificar si la respuesta tiene contenido
    if response.status_code == 204:
        return "Usuario añadido al grupo exitosamente"
    try:
        return response.json()
    except json.JSONDecodeError:
        print(f"Advertencia: No se pudo decodificar la respuesta JSON: {response.text}")
        return None

# Leer datos del Excel
df = pd.read_excel('RESULTS_FINAL.xlsx')

# Obtener token de acceso
access_token = get_access_token()

# 1. Crear grupos únicos con IDs personalizados
groups = df['GROUP'].unique()
group_ids = {}

for group in groups:
    group_data = {
        "displayName": group,
        "mailEnabled": False,
        "mailNickname": group.lower().replace(" ", "_"),
        "securityEnabled": True,
        "description": "ID: " + df[df['GROUP'] == group]['cn'].iloc[0]  # Almacenar el ID personalizado en la descripción
    }
    try:
        group_response = create_group(access_token, group_data)
        group_ids[group] = group_response['id']
        print(f"Grupo {group} creado con ID {group_response['id']}")
    except requests.exceptions.RequestException as e:
        print(f"Error al crear el grupo {group}: {e}")

# 2. Crear usuarios con IDs personalizados
for index, row in df.iterrows():
    user_data = {
        "accountEnabled": True,
        "displayName": row['displayName'],
        "givenName": row['givenName'],  # Asegúrate de incluir el givenName
        "mailNickname": row['givenName'],
        "userPrincipalName": row['mail'],
        "mail": row['mail'],
        "jobTitle": row['title'],
        "department": row['Entidad'],
        "country": "CO",  # Ajusta según corresponda
        "usageLocation": "CO",  # Debe ser un código de país ISO 3166-1 alpha-2
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": "P@ssw0rd123"
        },
        "passwordPolicies": "DisablePasswordExpiration"  # Ajuste adicional
    }

    print(f"Intentando crear usuario con datos: {user_data}")

    try:
        user_response = create_user(access_token, user_data)
        user_id = user_response['id']
        group_id = group_ids[row['GROUP']]

        # 3. Añadir usuario al grupo
        result = add_user_to_group(access_token, user_id, group_id)
        print(f"Resultado de añadir usuario al grupo: {result}")
        print(f"Usuario {row['displayName']} creado y añadido al grupo {row['GROUP']}")
    
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            print(f"Error al procesar el usuario {row['displayName']}: {e.response.text}")
        else:
            print(f"Error desconocido al procesar el usuario {row['displayName']}: {str(e)}")

print("Proceso completado.")
