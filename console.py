import cmd
import shlex
import models
import importlib
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
from models.trip_rider import TripRider
from models.total_payment import TotalPayment
from models.image import Image
from auth.authentication import _hash_password
import os
import sys
from models import storage
from sqlalchemy.exc import IntegrityError

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


class WegoCommand(cmd.Cmd):
    prompt = "(wego) "

    def do_EOF(self, arg):
        return True

    def emptyline(self):
        return False

    def do_quit(self, arg):
        return True

    def do_exit(self, arg):
        return True

    def do_clear(self, arg):
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    def _key_value_parser(self, args):
        """parses through args and conver it to dictionary representation
        by making class.id the key of a single instance"""
        new_dict = {}
        for arg in args:
            if "=" in arg:
                kvp = arg.split("=", 1)
                key = kvp[0]
                value = kvp[1]
                if len(value) > 0 and value[0] == value[-1] == '"':
                    value = shlex.split(value)[0].replace("_", " ")
                else:
                    try:
                        value = int(value)
                    except:
                        try:
                            value = float(value)
                        except:
                            try:
                                if "True" == value:
                                    value = True
                                elif "False" == value:
                                    value = False
                            except:
                                continue
                new_dict[key] = value
        return new_dict

    def do_create(self, arg):
        """creates an instance of a given class based on properies provided"""
        args = arg.split()
        if len(args) < 1:
            print("** class name missing **")
            return False
        if args[0] in classes:
            cols = classes[args[0]].__table__.columns.keys()

            parent_cols = ["id", "created_at", "updated_at"]
            if len(args) >= 1:
                new_dict = self._key_value_parser(args[1:])
                for k in cols:
                    if k not in new_dict.keys() and k not in parent_cols:
                        nullable = classes[args[0]].__table__.c[k].nullable
                        if not nullable:
                            print(f"{k}: is missing")
                            return False

                if args[0] in ["Rider", "Admin", "Driver"]:
                    try:
                        int(new_dict["phone_number"])
                    except:
                        print("** phone_number must be a number **")
                        return False
                    email = new_dict["email"]
                    phone_number = new_dict["phone_number"]
                    user_name = storage.get_all(args[0], username=new_dict["username"])
                    if user_name:
                        print("** username already exists **")
                        return False
                    user_email = storage.get_all(args[0], email=email)
                    if user_email:
                        print("** email already exists **")
                        return False
                    user_phone = storage.get_all(args[0], phone_number=phone_number)
                    if user_phone:
                        print("** phone_number already exists **")
                        return False
                    new_dict["password_hash"] = _hash_password(
                        new_dict["password_hash"]
                    )

                instance = classes[args[0]](**new_dict)
                instance.save()
                print(instance.id)
                # return instance.id
        else:
            print("** class doesn't exist **")
            return False

    def do_show(self, arg):
        """shows the whole table of instances and
        also a specific instance by id"""
        args = arg.split()
        data_dict = {}
        if len(args) < 1:
            print("** class name missing **")
            return False
        if args[0] in classes and len(args) >= 2:
            ar = args[1].split("=")
            kwargs = {ar[0]: ar[1]}
            data_dict = storage.get_all(args[0], **kwargs)
        elif args[0] in classes:
            data_dict = storage.get_all(args[0])
        else:
            print("** class doesn't exist **")
            return False
        if data_dict:
            for data in data_dict:
                data_dict[data] = data_dict[data].to_dict()
            print(data_dict)

    def do_destroy(self, arg):
        """to delete a single instance by the given class and instance id"""
        args = arg.split()
        if len(args) < 1:
            print("** class name missing **")
            return False
        elif len(args) < 2:
            print("** instance id missing **")
            return False
        elif args[0] in classes and len(args) == 2:
            try:
                storage.delete(args[0], args[1])
            except MemoryError:
                print("** unable to delete instance **")
                return False
            except Exception:
                print("** instance not found **")
                return False
            print(f"** {args[1]} Deleted **")
        else:
            print("** class doesn't exist **")
            return False

    def do_update(self, arg):
        """updates an instance based on a given class, id and the updates"""
        args = arg.split()
        if len(args) < 1:
            print("** class name missing **")
            return False
        if args[0] in classes:
            if len(args) < 2:
                print("** instance id missing **")
                return False
            if "id" in args[1]:
                id_dict = args[1].split("=")[1]

                if len(args) < 3:
                    print("** update argumnets missing **")
                    return False

                key = args[0] + "." + id_dict
                dict_data = self._key_value_parser(args[2:])
                if not dict_data or len(dict_data) != len(args) - 2:
                    print("** property or value incorrect **")
                    return False
                data = storage.get_all(args[0], id=id_dict)
                if not data:
                    print("** instance id doesn't exist **")
                    return False
                data = data[key]
                stop = False
                cols = classes[args[0]].__table__.columns.keys()
                for k in dict_data.keys():
                    if k not in cols:
                        print(f"** no property called {k} **")
                        stop = True
                if stop:
                    return False

                if "password_hash" in dict_data:
                    dict_data["password_hash"] = _hash_password(
                        dict_data["password_hash"]
                    )

                for k, v in dict_data.items():
                    setattr(data, k, v)
                data.save()
                print("saved")
            else:
                print('** "id" property missing **')
                return False
        else:
            print("** class doesn't exist **")
            return False

    def do_count(self, arg):
        """to count the number instances of a given class"""
        args = arg.split()
        if len(args) < 1:
            print("** class name missing **")
            return False
        elif args[0] == "all":
            for cls in classes:
                count = storage.count(cls)
                print(f"{cls}: {count}")
        elif args[0] in classes:
            count = storage.count(args[0])
            print(f"{args[0]}: {count}")
            # return count
        else:
            print("** class doesn't exist **")
            return False


if __name__ == "__main__":
    WegoCommand().cmdloop()
