"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import django
from django.test import TestCase

# TODO: Configure your database in settings.py and sync before running tests.

class SimpleTest(TestCase):
    """Tests for the application views."""

    # NOTE: django 1.8 and higher require calling setUpTestData()
    #       earlier: setUpClass()

    @classmethod
    def setUpTestData(cls):
        django.setup()
        return super().setUpTestData(cls)

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
