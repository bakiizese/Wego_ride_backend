#!/usr/bin/python3
import models
from models.base_model import Base
from models.availability import Availability
from models.driver import Driver
from models.location import Location
from models.rider import Rider
from models.driver import Driver
from models.payment import Payment
from models.trip import Trip
from models.notification import Notification
from models.vehicle import Vehicle
from models.admin import Admin
import sqlalchemy
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

mysql_user = 'wegoride_user'
mysql_host = 'localhost'
mysql_pwd = 'wegoride'
mysql_db = 'wego_db'

time = "%Y-%m-%dT%H:%M:%S.%f"

classes = {"Notification": Notification, "Driver": Driver, 
           "Rider": Rider, "Payment": Payment, "Trip": Trip,
           "Location": Location, "Availability": Availability,
           "Vehicle": Vehicle, "Admin": Admin}

class DBStorage:
    __engine = None
    __session = None

    def __init__(self) -> None:
        self.__engine = create_engine('mysql+mysqldb://{}:{}@{}/{}'
                                      .format('wegoride_user',
                                              'wegoride',
                                              'localhost',
                                              'wego_db'))
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def new(self, obj):
        """adds new obj or instance to the database"""
        self.__session.add(obj)

    def save(self):
        """saves the new added obj or instance"""
        self.__session.commit()

    def reload(self):
        """creates all the obj in the database"""
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def get(self, cls, **kwargs):
        '''returns class object that can be accessed by .'''
        return self.__session.query(classes[cls]).filter_by(**kwargs).first()
    
    def get_in_dict(self, cls, **kwargs):
        data_dict = self.get_all(classes[cls], **kwargs)
        for data in data_dict:
            data_dict[data] = data_dict[data].to_dict()
        return data_dict

    def get_all(self, cls, **kwargs):
        """returns all instance based on the class and id(optional)"""
        new_dict = {}
        if kwargs:
            try:
                data = self.__session.query(cls).filter_by(**kwargs)
            except exc.InvalidRequestError:
                print("** incorrect property in [{}] **".format(cls))
                return False
        else:
            data = self.__session.query(cls)
        for i in data:
            key = i.__class__.__name__ + '.' + i.id
            new_dict[key] = i
        return new_dict
    
    def delete(self, cls, arg=None):
        """deletes an instance based on the given class and id"""
        if arg:
            if "=" in arg:
                arg = arg.split("=")[1]
                if '"' in arg:
                    arg = arg.replace('"', "")
                elif "'" in arg:
                    arg = arg.replace("'", "")
            
            inst = self.__session.query(cls).get(arg)
            self.__session.delete(inst)
            self.save()
    
    def update(self, cls, id, **kwargs):
        cols = classes[cls].__table__.columns.keys()

        for k in kwargs.keys():
            if k not in cols:
                print("** key not found **")
                return False
        if 'username' in kwargs:
            user = self.get(cls, username=kwargs['username'])
            if user:
                print("** username already exist **")
                return False

        for k, v in kwargs.items():
            self.__session.query(classes[cls]).filter(classes[cls].id == id).update(
                {k: v},
                synchronize_session=False,
                )
            self.save()

    def count(self, arg):
        """returns the number of instances in a given class"""
        data = self.get_all(arg)
        return len(data)