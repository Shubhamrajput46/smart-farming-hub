from django.test import SimpleTestCase
from .paginator import StandardResultsSetPagination

class ApiConfigurationTests(SimpleTestCase):
    def test_pagination_defaults(self):
        paginator = StandardResultsSetPagination()
        self.assertEqual(paginator.page_size, 10)
        self.assertEqual(paginator.max_page_size, 100)
