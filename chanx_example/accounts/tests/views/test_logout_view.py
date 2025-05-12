from django.urls import reverse

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from test_utils.auth_api_test_case import AuthAPITestCase


class LogoutViewTestCase(AuthAPITestCase):
    url = reverse("custom_rest_logout")

    def test_logout_no_refresh_cookie(self) -> None:
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_logout_with_refresh_cookie(self) -> None:
        """Test logout with refresh cookie in the request."""
        # Set a cookie with the JWT refresh token name from settings

        assert BlacklistedToken.objects.count() == 0
        self.auth_client.post(self.url)

        assert BlacklistedToken.objects.count() == 1
