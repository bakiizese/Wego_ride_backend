from models.engine import db_storage
from models.driver import Driver
from auth import authentication
from models import storage
import unittest
import console

WegoCommand = console.WegoCommand()
Auth = authentication.Auth()
kwargs = {'username': 'bereket',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'bereketzese@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}


class TestDBStorage(unittest.TestCase):
    '''test all main funcs in db_storage'''
    def test_get_all(self):
        '''test to get a user from db based on given params'''
        user = Auth.register_user('Driver', **kwargs)

        get_user1 = storage.get_all(Driver)
        get_user2 = storage.get_all(Driver, phone_number=90909)
        get_user3 = storage.get_all(Driver, jack="wrong")

        self.assertEqual(type(get_user1), dict)
        self.assertEqual(type(get_user2), dict)
        self.assertEqual(get_user3, False)

        WegoCommand.do_destroy(f'Driver id={user}')


    def test_delete(self):
        '''test delete function if it actually deletes by the given param'''
        user = Auth.register_user('Driver', **kwargs)
        count = storage.count(Driver)
        
        storage.delete(Driver, f'id={user}')

        count2 = storage.count(Driver)
        self.assertLessEqual(count2, count)


    def test_update(self):
        '''test update def by the given updates and instance id'''
        user = Auth.register_user('Driver', **kwargs)
        username1 = storage.get('Driver', id=user).username
    
        storage.update('Driver', user, username="jaki")
        
        username2 = storage.get('Driver', id=user).username

        self.assertEqual(username2, 'jaki')
        self.assertNotEqual(username1, username2)

        storage.delete(Driver, f'id={user}')