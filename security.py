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
        self.server_url = os.environ.get('KEYCLOAK_URL', 'http://localhost:8080')
        self.realm_name = os.environ.get('KC_REALM', 'catequesis-realm')
        self.client_id = os.environ.get('KC_CLIENT_ID', 'catequesis-app')
        self.client_secret = os.environ.get('KC_CLIENT_SECRET', '')
        
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=self.client_secret
        )

    def get_login_url(self, redirect_uri):
        return self.keycloak_openid.auth_url(
            redirect_uri=redirect_uri,
            scope="openid profile email"
        )

    def get_token(self, code, redirect_uri):
        return self.keycloak_openid.token(
            grant_type='authorization_code',
            code=code,
            redirect_uri=redirect_uri
        )

    def get_user_info(self, token):
        return self.keycloak_openid.userinfo(token)

    def get_logout_url(self, redirect_uri):
        return f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/logout?post_logout_redirect_uri={redirect_uri}&client_id={self.client_id}"

keycloak_manager = KeycloakManager()
