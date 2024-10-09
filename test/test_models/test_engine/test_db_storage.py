from models.engine import db_storage
from models.driver import Driver
from auth import authentication
import unittest
import console

WegoCommand = console.WegoCommand()
Auth = authentication.Auth()
DBStorage = db_storage.DBStorage()

kwargs = {'username': 'bereket',
                    'first_name': 'berekete',
                    'last_name': 'zeselassie',
                    'email': 'bereketzese@gmail.com',
                    'phone_number': 90909,
                    'password_hash': 'mypass'}
user_id = None

class TestDBStorage(unittest.TestCase):
    def test_get_all(self):
        '''test to get a user from db based on given params'''
        global user_id

        user = Auth.register_user('Driver', **kwargs)
        user_id = user
        get_user1 = DBStorage.get_all(Driver)
        get_user2 = DBStorage.get_all(Driver, phone_number=90909)
        get_user3 = DBStorage.get_all(Driver, jack="wrong")

        self.assertEqual(type(get_user1), dict)
        self.assertEqual(type(get_user2), dict)
        self.assertEqual(get_user3, False)

        WegoCommand.do_destroy(f'Driver id={user}')

    def test_delete(self):
        '''test delete function if it actually deletes by the given param'''
        user = Auth.register_user('Driver', **kwargs)
        count = DBStorage.count(Driver)
        
        DBStorage.delete(Driver, f'id={user}')

        count2 = DBStorage.count(Driver)
        self.assertLessEqual(count2, count)

    # def test_update(self):
    #     user = Auth.register_user('Driver', **kwargs)
    #     username1 = WegoCommand.do_show(f'Driver id={user}')
    #     for i in username1:
    #         username1 = i.username
    #     print(f'\n\n\n\{username1}\n\n')
    #     DBStorage.update('Driver', user, username="jaki")
    #     # username2 = DBStorage.get(Driver, id=user)['username']

    #     # self.assertEqual(username2, 'jaki')
    #     # self.assertNotEqual(username1, username2)

    #     DBStorage.delete(Driver, f'id={user}')

