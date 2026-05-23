import os
from keycloak import KeycloakOpenID
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name, email, roles):
        self.id = id
        self.name = name
        self.email = email
        self.roles = roles

class KeycloakManager:
    def __init__(self):
        # URL para redirecciones en el navegador (ej: localhost:8080)
        self.server_url = os.environ.get('KEYCLOAK_URL', 'http://localhost:8080')
        # URL para comunicación interna entre contenedores (ej: keycloak:8080)
        self.internal_url = os.environ.get('KEYCLOAK_INTERNAL_URL', self.server_url)
        
        self.realm_name = os.environ.get('KC_REALM', 'catequesis-realm')
        self.client_id = os.environ.get('KC_CLIENT_ID', 'catequesis-app')
        self.client_secret = os.environ.get('KC_CLIENT_SECRET', '')
        
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.internal_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=self.client_secret
        )

    def get_login_url(self, redirect_uri):
        # Usamos la URL externa para que el navegador del usuario pueda llegar
        auth_url = self.keycloak_openid.auth_url(
            redirect_uri=redirect_uri,
            scope="openid profile email"
        )
        return auth_url.replace(self.internal_url, self.server_url)

    def get_logout_url(self, redirect_uri):
        # Usamos la URL externa para el logout
        return f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/logout?post_logout_redirect_uri={redirect_uri}&client_id={self.client_id}"

    def get_token(self, code, redirect_uri):
        return self.keycloak_openid.token(
            grant_type='authorization_code',
            code=code,
            redirect_uri=redirect_uri
        )

    def get_user_info(self, token):
        return self.keycloak_openid.userinfo(token)

keycloak_manager = KeycloakManager()
