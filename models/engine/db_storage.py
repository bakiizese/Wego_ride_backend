#!/usr/bin/python
from models.base_model import Base
from models.availability import Availability
from models.driver import Driver
from models.location import Location
from models.rider import Rider
from models.payment import Payment
from models.trip import Trip
from models.notification import Notification
from models.vehicle import Vehicle
from models.admin import Admin
from models.trip_rider import TripRider
from models.total_payment import TotalPayment
from models.image import Image
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

from config import settings

time = "%Y-%m-%dT%H:%M:%S.%f"


def _default_db_url():
    return "mysql+pymysql://{}:{}@{}:{}/{}".format(
        settings.db_user,
        settings.db_password,
        settings.db_host,
        settings.db_port,
        settings.db_name,
    )


classes = {
    "Notification": Notification,
    "Driver": Driver,
    "Rider": Rider,
    "Payment": Payment,
    "Trip": Trip,
    "Location": Location,
    "Availability": Availability,
    "Vehicle": Vehicle,
    "Admin": Admin,
    "TripRider": TripRider,
    "TotalPayment": TotalPayment,
    "Image": Image,
}


class DBStorage:
    __engine = None
    __session = None

    def __init__(self, db_url=None) -> None:
        self.configure(db_url or _default_db_url())

    def configure(self, db_url):
        """(Re)point this instance at a database and reload the session.
        Used directly by tests to redirect the process-wide `storage`
        singleton to an isolated test database in place - mutating the
        existing object works regardless of how many modules already
        hold a `from models import storage` reference to it."""
        connect_args = {}
        if settings.db_ssl_ca:
            connect_args["ssl"] = {"ca": settings.db_ssl_ca}
        self.__engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=280,
            pool_size=5,
            max_overflow=10,
            connect_args=connect_args,
        )
        self.reload()

    def new(self, obj):
        """adds new obj or instance to the database"""
        self.__session.add(obj)

    def save(self):
        """saves the new added obj or instance"""
        try:
            self.__session.commit()
        except Exception:
            self.__session.rollback()
            raise

    def reload(self):
        """creates all the obj in the database"""
        if settings.auto_create_tables:
            Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def rollback(self):
        """rollback any form commit"""
        self.__session.rollback()

    def get(self, cls, **kwargs):
        """returns class object that can be accessed by ."""
        return self.__session.query(classes[cls]).filter_by(**kwargs).first()

    def get_objs(self, cls, **kwargs):
        """returns class object that can be accessed by ."""
        if kwargs:
            return self.__session.query(classes[cls]).filter_by(**kwargs)
        return self.__session.query(classes[cls])

    def get_in_dict(self, cls, **kwargs):
        data_dict = self.get_all(cls, **kwargs)
        for data in data_dict:
            data_dict[data] = data_dict[data].to_dict()
        return data_dict

    def get_all(self, cls, **kwargs):
        """returns all instance based on the class and id(optional)"""
        new_dict = {}
        if kwargs:
            try:
                data = self.__session.query(classes[cls]).filter_by(**kwargs)
            except exc.InvalidRequestError:
                print("** incorrect property in [{}] **".format(classes[cls]))
                return False
        else:
            data = self.__session.query(classes[cls])
        for i in data:
            key = i.__class__.__name__ + "." + i.id
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
            try:
                inst = self.__session.query(classes[cls]).filter_by(id=arg).first()
                self.__session.delete(inst)
                self.save()
            except Exception:
                self.__session.rollback()
                raise

    def update(self, cls, id, **kwargs):
        cols = classes[cls].__table__.columns.keys()
        for k in kwargs.keys():
            if k not in cols:
                print("** key not found **")
                return False
        if "username" in kwargs:
            user = self.get(cls, username=kwargs["username"])
            if user:
                print("** username already exist **")
                return False

        self.__session.query(classes[cls]).filter(classes[cls].id == id).update(
            kwargs,
            # "fetch" keeps the session's identity map in sync, so a
            # storage.get() for this id right after this update() doesn't
            # return a stale cached object (synchronize_session=False was
            # silently doing that)
            synchronize_session="fetch",
        )
        self.save()

    def count(self, arg):
        """returns the number of instances in a given class"""
        data = self.get_all(arg)
        return len(data)
