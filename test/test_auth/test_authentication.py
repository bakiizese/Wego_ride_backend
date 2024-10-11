import unittest
import io
import sys
from parameterized import parameterized
from auth import authentication
import console
from models import storage
from models.driver import Driver

WegoCommand = console.WegoCommand()
Auth = authentication.Auth()
user_id = None


class TestAuthentication(unittest.TestCase):
    '''authentication test returns and prints'''
    @parameterized.expand([
        ('Driver', {'username': 'bereket',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'bereketzese@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}, '', None),
        ('Driver', {'username': 'bereket',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'bereketzese@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}, '** username already exists **', False),
        ('Driver', {'username': 'berek',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'bereketzese@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}, '** email already exists **', False),
        ('Driver', {'username': 'beket',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'berekete@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}, '** phone number already exists **', False)
    ])
    def test_register_user(self, cls, kwargs, expected_print, expected_return):
        global user_id
        captured_output = io.StringIO()
        sys.stdout = captured_output

        user = Auth.register_user(cls, **kwargs)
        
        sys.stdout = sys.__stdout__

        if not user:
            self.assertEqual(captured_output.getvalue().strip(), expected_print)
            self.assertEqual(user, expected_return)
        else:
            user = storage.get('Driver', email="bereketzese@gmail.com")
            user_id = user.id
            if user:
                self.assertNotEqual(user.password_hash, 'mypass')
    

    def test_update_password(self):
        '''test id update_password really updates 
        password by the given reset token and email'''
        reset_token = Auth.create_reset_token('Driver', email='bereketzese@gmail.com')
        pre_password = storage.get('Driver', email='bereketzese@gmail.com').password_hash
        Auth.update_password('Driver', reset_token, "new_password")
        post_password = storage.get('Driver', email='bereketzese@gmail.com').password_hash
        
        self.assertNotEqual(pre_password, post_password)
        
    def test_verify_login(self):
        '''verify login by the given passcode and email'''
        login = Auth.verify_login('Driver', 'bereketzese@gmail.com', 'new_password')
        login2 = Auth.verify_login('Driver', 'bereketzese@gmail.com', 'ss')
        login3 = Auth.verify_login('Driver', 'bere@gmail.com', 'mypass')
        
        self.assertEqual(login, True)
        self.assertEqual(login2, False)
        self.assertEqual(login3, False)
    
    @classmethod
    def tearDownClass(cls):
        if user_id:
            WegoCommand.do_destroy(f'Driver id={user_id}')