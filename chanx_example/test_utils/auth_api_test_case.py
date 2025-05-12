from rest_framework.test import APIClient, APITestCase

from dj_rest_auth.app_settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.factories.user import UserFactory


class AuthAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory.create(email="user@mail.com")
        self.user.save()

        user_refresh_token = RefreshToken.for_user(self.user)

        self.auth_client = APIClient()
        self.auth_client.cookies[jwt_settings.JWT_AUTH_COOKIE] = str(
            user_refresh_token.access_token
        )
        self.auth_client.cookies[jwt_settings.JWT_AUTH_REFRESH_COOKIE] = str(
            user_refresh_token
        )
