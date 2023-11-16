from django.test import TestCase
from goodreads import urls
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class TestAuthenticatedViews(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='testuser', password='testpassword')

class TestAllUrls(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='testuser', password='testpassword')

    def test_urls(self):
        # Test that all URLs are accessible by an authenticated user
        self.client.login(username='testuser', password='testpassword')
        test_file = SimpleUploadedFile("test.txt", b"file_content")

        # Mock form data and include in the file upload
        form_data = {
            'field1': 'value1',  # Add other form fields as needed
            'file_field': test_file,
        }
        # List of URL patterns to be tested
        url_patterns = urls.urlpatterns

        for u in url_patterns[3:]:
            url_pattern = u.pattern
            url_name = u.name
            print(url_name)
            try:
                url = reverse(url_name)
                response = self.client.get(url, file=form_data)
                self.assertEqual(response.status_code, 200)  # Adjust the status code as needed
            except NoReverseMatch:
                self.fail(f"URL pattern '{url_pattern}' could not be reversed.")
