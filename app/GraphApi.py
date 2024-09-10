import requests
import json
import pandas as pd
import time
import math
from urllib.parse import urlencode
from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Configuración de autenticación
tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

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

# Función para agregar múltiples usuarios a un grupo utilizando batch requests
def add_users_to_group_batch(access_token, group_id, user_ids):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    batch_size = 20  # Tamaño máximo permitido por batch request
    total_batches = math.ceil(len(user_ids) / batch_size)

    for i in range(total_batches):
        batch_request = {
            "requests": []
        }

        start_index = i * batch_size
        end_index = start_index + batch_size
        batch_user_ids = user_ids[start_index:end_index]

        # Construir las solicitudes para cada usuario en el batch
        for j, user_id in enumerate(batch_user_ids):
            batch_request["requests"].append({
                "id": f"{i}-{j}",
                "method": "POST",
                "url": f"/groups/{group_id}/members/$ref",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
                }
            })

        # Enviar la solicitud batch
        url = f"{graph_url}/$batch"
        response = requests.post(url, headers=headers, json=batch_request, verify=False)
        response.raise_for_status()

        # Manejar la respuesta
        results = response.json().get('responses', [])
        for result in results:
            if result.get('status') != 204:  # 204 No Content indica éxito
                print(f"Error al agregar usuario con ID {batch_user_ids[int(result['id'].split('-')[1])]}: {result.get('body')}")

# Función para obtener todos los miembros de un grupo con paginación
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

# Obtener los roles de la aplicación
def get_app_roles(access_token, service_principal_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/servicePrincipals/{service_principal_id}/appRoles"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()
    return data.get('value', [])  # Asegúrate de que retorna una lista

# Verificar si el grupo ya tiene asignado el rol
def is_group_assigned_to_role(access_token, group_id, service_principal_id, app_role_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Obtener todas las asignaciones de roles para este service principal
    url = f"{graph_url}/servicePrincipals/{service_principal_id}/appRoleAssignments"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    assignments = response.json().get('value', [])

    # Filtrar localmente para verificar si el grupo ya tiene el rol asignado
    for assignment in assignments:
        if assignment['principalId'] == group_id and assignment['appRoleId'] == app_role_id:
            return True
    return False

# Asignar grupo al rol `msiam_access` de la aplicación
def assign_group_to_app_role(access_token, group_name, group_id, service_principal_id, app_role_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = f"{graph_url}/servicePrincipals/{service_principal_id}/appRoleAssignments"
    body = {
        "principalId": group_id,
        "resourceId": service_principal_id,
        "appRoleId": app_role_id
    }
    try:
        response = requests.post(url, headers=headers, json=body, verify=False)
        response.raise_for_status()
        print(f"Grupo {group_name} asignado al rol `msiam_access` de la Enterprise Application.")
    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        if error_response.get('error', {}).get('message') == 'Permission being assigned already exists on the object':
            print(f"El grupo {group_name} ya tiene asignado el rol `msiam_access` y no será agregado nuevamente.")
        else:
            raise

# ID de la Enterprise Application "API-driven provisioning to Microsoft Entra ID"
service_principal_id = '1b448c25-42f9-4200-b514-578835f61fe1'

# Leer datos del CSV en lugar del Excel
df = pd.read_csv('CONSOLIDADO.csv', delimiter=';')

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

    # Recopilar los usuarios que no están en el grupo
    users_to_add = []
    for index, row in df[df['GROUP'] == group].iterrows():
        user = get_user_by_email(access_token, row['mail'])
        if user and user['id'] not in current_members:
            users_to_add.append(user['id'])
        elif not user:
            print(f"Usuario con correo {row['mail']} no encontrado en Azure AD")

    # Agregar usuarios al grupo en batch
    if users_to_add:
        add_users_to_group_batch(access_token, group_id, users_to_add)
        print(f"Usuarios añadidos al grupo {group}: {users_to_add}")

# 3. Obtener los roles de la aplicación y encontrar el rol `msiam_access`
app_roles = get_app_roles(access_token, service_principal_id)
print(f"Roles obtenidos: {app_roles}")

msiam_access_role = next((role for role in app_roles if role['displayName'] == 'msiam_access'), None)

if msiam_access_role:
    app_role_id = msiam_access_role['id']
    # Asignar grupos al rol `msiam_access`
    for group_name, group_id in group_ids.items():
        try:
            if is_group_assigned_to_role(access_token, group_id, service_principal_id, app_role_id):
                print(f"El grupo {group_name} ya hace parte del Enterprise Application con rol `msiam_access`.")
            else:
                assign_group_to_app_role(access_token, group_name, group_id, service_principal_id, app_role_id)
        except requests.exceptions.HTTPError as e:
            error_response = e.response.json()
            print(f"Error al asignar el grupo {group_name} al rol `msiam_access`: {error_response}")
else:
    print("El rol `msiam_access` no se encontró en la Enterprise Application.")

print("Proceso de asignación completado.")
