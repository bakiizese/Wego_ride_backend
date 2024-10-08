import unittest
import console
from models import storage
from parameterized import parameterized
WegoCommand = console.WegoCommand()

class TestConsole(unittest.TestCase):

    @parameterized.expand([
        (['email="bereket@gmail.com"'], {"email": "bereket@gmail.com"}),
        (['email'], {}),
        (['email=1234'], {'email': 1234}),
        (['email="1234"'], {'email': '1234'}),
        (['email="12.34"'], {'email': '12.34'}),
        (['email=baki'], {}),
        (["email='baki'"], {}),
        (["email="], {}),
        ("email", {}),
    ])
    def test_key_value_parser(self, args, expected):
        dict_data = WegoCommand._key_value_parser(args)
        self.assertEqual(type(dict_data), dict)
        self.assertEqual(dict_data, expected)


    def test_console(self):
        num = 12344
        arg = f'Driver username="bak" first_name="bere" last_name="zese" email="bere@z" phone_number={num} password_hash="password"'
        user = WegoCommand.do_create(arg)

        user_count1 = WegoCommand.do_count('Driver')
        user_check = storage.get('Driver', email="bere@z")
        user_count2 = WegoCommand.do_count('Driver')

        self.assertLessEqual(user_count1, user_count1)
        self.assertEqual(user, user_check.id)

        user_delete = WegoCommand.do_destroy(f'Driver id={user_check.id}')
        user_check = storage.get('Driver', email="bere@z")
        user_count3 = WegoCommand.do_count('Driver')

        self.assertEqual(user_check, None)
        self.assertLessEqual(user_count3, user_count2)
    
        user_update = WegoCommand.do_update()