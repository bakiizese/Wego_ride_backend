import io
import sys
import unittest
import console
from models import storage
from parameterized import parameterized
WegoCommand = console.WegoCommand()

user_id = None

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
        '''test if it returns a dict data type by receiving string type'''
        dict_data = WegoCommand._key_value_parser(args)
        self.assertEqual(type(dict_data), dict)
        self.assertEqual(dict_data, expected)

    @parameterized.expand([
        ("", '** class name missing **', False),
        ('Drive', '** class doesn\'t exist **', False),
        ('Driver', 'username: is missing', False),
        ('Driver username="bekii"', 'first_name: is missing', False),
        ('Driver username="bekii" first_name="bereket"', 'last_name: is missing', False),
        (f'Driver username="bekii" first_name="bereket" last_name="zesess" email="bereket@bereket" phone_number={123456} password_hash="passcode"', '', ''),
        (f'Driver username="bekii" first_name="bereket" last_name="zesess" email="bereket@bereket" phone_number={123456} password_hash="passcode"', '** username already exists **', False),
        (f'Driver username="beki" first_name="bereket" last_name="zesess" email="bereket@bereket" phone_number={123456} password_hash="passcode"', '** email already exists **', False),
        (f'Driver username="beki" first_name="bereket" last_name="zesess" email="bereket@ereket" phone_number={123456} password_hash="passcode"', '** phone_number already exists **', False),
        ('Driver username="beki" first_name="bereket" last_name="zesess" email="bereket@reket" phone_number="1236" password_hash="passcode"', '** phone_number must be a number **', False)
    ])
    def test_do_create(self, arg, expected_print, expected_return):
        global user_id

        captured_output = io.StringIO()
        sys.stdout = captured_output

        user = WegoCommand.do_create(arg)

        sys.stdout = sys.__stdout__
        if not user:
            self.assertEqual(captured_output.getvalue().strip(), expected_print)
            self.assertEqual(user, expected_return)
        else:
            user_id = user
    
    @parameterized.expand([
        ('', '** class name missing **', False),
        ('Dr', '** class doesn\'t exist **', False),
        ('Driver id=adad', '', None)
        ])
    def test_do_show(self, arg, expected_print, expected_return):
        captured_output = io.StringIO()
        sys.stdout = captured_output

        data_dict = WegoCommand.do_show(arg)
        
        sys.stdout = sys.__stdout__

        self.assertEqual(captured_output.getvalue().strip(), expected_print)
        self.assertEqual(data_dict, expected_return)

    @parameterized.expand([
        ('', '** class name missing **', False),
        ('Drivr', '** class doesn\'t exist **', False),
        ('Driver', '** instance id missing **', False),
        ('Driver adsasd', '** "id" property missing **', False),
        ('Driver id=asdasd', '** update argumnets missing **', False),
        ('Driver i=asdsads used="jack"', '** \"id\" property missing **', False),
        ('Driver id=asdsads username="jack"', '** instance id doesn\'t exist **', False),
        ])
    def test_do_update(self, arg, expected_print, expected_return):
        captured_output = io.StringIO()
        sys.stdout = captured_output
       
        update = WegoCommand.do_update(arg)

        sys.stdout = sys.__stdout__

        self.assertEqual(captured_output.getvalue().strip(), expected_print)
        self.assertEqual(update, expected_return)


    def test_console(self):
        '''Integration test for the whole console'''
        num = 12344
        arg = f'Driver username="bak" first_name="bere" last_name="zese" email="bere@z" phone_number={num} password_hash="password"'
        user = WegoCommand.do_create(arg)

        user_count1 = WegoCommand.do_count('Driver')
        user_check = storage.get('Driver', email="bere@z")
        user_count2 = WegoCommand.do_count('Driver')

        self.assertLessEqual(user_count1, user_count1)
        self.assertEqual(user, user_check.id)
        self.assertNotEqual(user_check.first_name, 'baki')
        
        user_update = WegoCommand.do_update(f'Driver id={user_check.id} first_name="baki"')
        first_name_check = storage.get('Driver', id=user_check.id)

        self.assertEqual(first_name_check.first_name, 'baki')
        self.assertEqual(first_name_check.first_name, user_check.first_name)

        user_delete = WegoCommand.do_destroy(f'Driver id={user_check.id}')
        user_check = storage.get('Driver', email="bere@z")
        user_count3 = WegoCommand.do_count('Driver')

        self.assertEqual(user_check, None)
        self.assertLessEqual(user_count3, user_count2)
    
    @classmethod
    def tearDownClass(cls):
        if user_id:
            WegoCommand.do_destroy(f'Driver id={user_id}')