from rest_framework.test import APIClient, APITestCase

from asgiref.sync import sync_to_async
from dj_rest_auth.app_settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.factories.user import UserFactory
from accounts.models import User


class AuthAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory.create(email="user@mail.com")
        self.user.save()

        self.jwt_settings = jwt_settings  # Make JWT settings accessible as a property
        user_refresh_token = RefreshToken.for_user(self.user)

        self.auth_client = APIClient()
        self.auth_client.cookies[jwt_settings.JWT_AUTH_COOKIE] = str(
            user_refresh_token.access_token
        )
        self.auth_client.cookies[jwt_settings.JWT_AUTH_REFRESH_COOKIE] = str(
            user_refresh_token
        )

    @classmethod
    def get_client_for_user(cls, user: User) -> APIClient:
        """
        Create an authenticated API client for a specific user.

        Args:
            user: The user to authenticate as

        Returns:
            An authenticated APIClient instance
        """
        client = APIClient()
        refresh_token = RefreshToken.for_user(user)

        client.cookies[jwt_settings.JWT_AUTH_COOKIE] = str(refresh_token.access_token)
        client.cookies[jwt_settings.JWT_AUTH_REFRESH_COOKIE] = str(refresh_token)

        return client

    @classmethod
    async def aget_client_for_user(cls, user: User) -> APIClient:
        return await sync_to_async(cls.get_client_for_user)(user)
