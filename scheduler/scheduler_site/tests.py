from django.test import TestCase

from .models import Account

class AccountTest(TestCase):
    def test_matchName(self):
        name = "Jimothy"
        n = Account(name=name)
        self.assertEqual(name, n.__str__(), "Account name does not equal entered name")