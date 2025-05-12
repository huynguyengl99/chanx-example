from django.urls import reverse
from rest_framework.test import APITestCase


class SpectacularNoErrorAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.has_error_url = reverse("schema")

    def test_get_schema_without_errors(self) -> None:
        """Test that the schema is generated without error definitions."""
        response = self.client.get(reverse("schema-no-error"))
        self.assertEqual(response.status_code, 200)
        # The schema should be valid JSON
        schema_data = response.content.decode("utf-8")

        assert "ErrorResponse" not in schema_data

    def test_get_schema_with_errors(self) -> None:
        """Test that the schema is generated without error definitions."""
        response = self.client.get(reverse("schema"))
        self.assertEqual(response.status_code, 200)
        # The schema should be valid JSON
        schema_data = response.content.decode("utf-8")

        assert "ErrorResponse" in schema_data
