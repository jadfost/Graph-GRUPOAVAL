import requests
import json
import pandas as pd
import time

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

# Verificar si el grupo existe
def get_group_by_name(access_token, group_name):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups?$filter=displayName eq '{group_name}'"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    groups = response.json().get('value', [])
    return groups[0] if groups else None

# Crear grupo
def create_group(access_token, group_data):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups"
    response = requests.post(url, headers=headers, json=group_data, verify=False)
    response.raise_for_status()
    return response.json()

# Buscar usuario por correo
def get_user_by_email(access_token, email):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/users?$filter=mail eq '{email}'"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    users = response.json().get('value', [])
    return users[0] if users else None

# Obtener todos los miembros de un grupo
def get_group_members(access_token, group_id):
    members = []
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups/{group_id}/members"
    while url:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        members.extend(data.get('value', []))
        url = data.get('@odata.nextLink', None)
    return {member['id'] for member in members}

# Añadir usuario al grupo
def add_user_to_group(access_token, user_id, group_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/groups/{group_id}/members/$ref"
    body = {
        "@odata.id": f"{graph_url}/directoryObjects/{user_id}"
    }
    response = requests.post(url, headers=headers, json=body, verify=False)
    response.raise_for_status()

# Leer datos del Excel
df = pd.read_excel('RESULTS_FINAL.xlsx')

# Obtener token de acceso
access_token = get_access_token()

# 1. Verificar y crear grupos si no existen
group_ids = {}
for group in df['GROUP'].unique():
    existing_group = get_group_by_name(access_token, group)
    if existing_group:
        group_ids[group] = existing_group['id']
        print(f"El grupo {group} ya existe con ID {existing_group['id']}")
    else:
        group_data = {
            "displayName": group,
            "mailEnabled": False,
            "mailNickname": group.lower().replace(" ", "_"),
            "securityEnabled": True,
        }
        group_response = create_group(access_token, group_data)
        group_ids[group] = group_response['id']
        print(f"Grupo {group} creado con ID {group_response['id']}")

# 2. Obtener los IDs de los usuarios y preparar para la inserción
for group, group_id in group_ids.items():
    # Obtener los miembros actuales del grupo
    current_members = get_group_members(access_token, group_id)

    # Filtrar usuarios que no estén ya en el grupo
    for index, row in df[df['GROUP'] == group].iterrows():
        user = get_user_by_email(access_token, row['mail'])
        if user:
            if user['id'] not in current_members:
                try:
                    add_user_to_group(access_token, user['id'], group_id)
                    print(f"Usuario {row['mail']} añadido al grupo {group}")
                except requests.exceptions.HTTPError as e:
                    print(f"Error al añadir el usuario {row['mail']} al grupo {group}: {e}")
            else:
                print(f"El usuario {row['mail']} ya es miembro del grupo {group}")
        else:
            print(f"Usuario con correo {row['mail']} no encontrado en Azure AD")

print("Proceso completado.")
