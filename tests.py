import unittest

from app.models import User
from app.utils import seconds_to_decimal, seconds_to_string


class UtilsCase(unittest.TestCase):
    def test_seconds_to_string(self):
        self.assertEqual(seconds_to_string(0), "0s")
        self.assertEqual(seconds_to_string(1), "1s")
        self.assertEqual(seconds_to_string(59), "59s")
        self.assertEqual(seconds_to_string(60), "1 min")
        self.assertEqual(seconds_to_string(3599), "59 min")
        self.assertEqual(seconds_to_string(3600), "1 h 0 min")
        self.assertEqual(seconds_to_string(86399), "23 h 59 min")
        self.assertEqual(seconds_to_string(86400), "24 h 0 min")
        self.assertEqual(seconds_to_string(604799), "167 h 59 min")
        self.assertEqual(seconds_to_string(604800), "168 h 0 min")

    def test_seconds_to_decimal(self):
        self.assertEqual(seconds_to_decimal(0), 0.0)
        self.assertEqual(seconds_to_decimal(1), 0.0)
        self.assertEqual(seconds_to_decimal(59), 0.01)
        self.assertEqual(seconds_to_decimal(60), 0.01)
        self.assertEqual(seconds_to_decimal(3599), 0.99)
        self.assertEqual(seconds_to_decimal(3600), 1.0)
        self.assertEqual(seconds_to_decimal(86399), 23.99)
        self.assertEqual(seconds_to_decimal(86400), 24.0)
        self.assertEqual(seconds_to_decimal(604799), 167.99)
        self.assertEqual(seconds_to_decimal(604800), 168.0)


class UserModelCase(unittest.TestCase):
    def test_password_hashing(self):
        user = User(
            email_address="mash@example.com", password="8wCS0H65r@p!8%B0XxrPTbBiR%^tc##f", timezone="Europe/London"
        )
        self.assertFalse(user.check_password("Haxx0rz"))
        self.assertTrue(user.check_password("8wCS0H65r@p!8%B0XxrPTbBiR%^tc##f"))


if __name__ == "__main__":
    unittest.main(verbosity=2)