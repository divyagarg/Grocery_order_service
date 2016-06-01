__author__ = 'amit.bansal'

import datetime
from config import APP_NAME
import copy
import json
import logging
import jsonpickle

Logging = logging.getLogger(APP_NAME)

def json_serial(obj):
	if isinstance(obj, datetime.datetime):
		serial = obj.isoformat()
		return serial
	raise TypeError("Type not serializable")


class JsonUtility(object):
    """
	   This class provide the functionality of converting json object to json
	   and json to respected json object

	"""

    """
		convert python object to json with py/object key in it
	"""

    def get_raw_json(self):
        string_json = jsonpickle.encode(self)
        pure_json = json.loads(string_json)
        return pure_json

    """
		convert python object to json with only field defined in class
	"""

    def get_json(self, pure_json=None, skip_keys_with_none = False):
        if pure_json == None:
            pure_json = self.get_raw_json()

        if isinstance(pure_json, dict):
            for key, value in pure_json.items():

                if isinstance(value, list):
                    for val in value:
                        self.get_json(pure_json=val, skip_keys_with_none=skip_keys_with_none)

                if isinstance(value, dict):
                    self.get_json(pure_json=value, skip_keys_with_none=skip_keys_with_none)

                if key == 'py/object' or str(key).startswith("__"):
                    pure_json.pop(key, None)

                elif pure_json[key] is None and skip_keys_with_none == True:
                    pure_json.pop(key, None)

        elif isinstance(pure_json, list):
            for val in pure_json:
                self.get_json(val,  skip_keys_with_none=skip_keys_with_none)

        return pure_json

    """
		takes pure json object and convert it to decodable json
		basically append py/object in dict with respected class
	"""

    @classmethod
    def get_decodable_json(cls, pure_json, skip_keys_with_none=False, class_object=None):

        if isinstance(pure_json, dict):

            if class_object == None:
                class_object = cls

            if 'class' in str(class_object):
                class_name = str(class_object).split("'")[1]
            else:
                class_name = str(class_object).strip("<>'\" ")

            pure_json['py/object'] = class_name

            for key, value in pure_json.items():
                if isinstance(value, dict):
                    class_obj = cls.get_classes(key)
                    if class_obj:
                        class_obj.get_decodable_json(value, skip_keys_with_none=skip_keys_with_none, class_object=class_obj)

                elif isinstance(value, list):
                    for item in value:
                        class_obj = cls.get_classes(key)
                        if class_obj:
                            class_obj.get_decodable_json(item,  skip_keys_with_none=skip_keys_with_none, class_object=class_obj)

            return pure_json

    @classmethod
    def get_object(cls, pure_json, ignore_extra_keys=False):
        if isinstance(pure_json, dict):
            cls.validate_object(pure_json.copy(), ignore_extra_keys=ignore_extra_keys)
            decodable_json = cls.get_decodable_json(pure_json=pure_json, skip_keys_with_none=False)
            decodable_string = json.dumps(decodable_json)
            obj = jsonpickle.decode(decodable_string)
            obj.assign_default_values()
            return obj
        else:
            raise Exception('Invalid Json format')

    @classmethod
    def get_classes(cls, key):
        return None

    def clone(self):
        return copy.deepcopy(self)

    def is_valid(self):
        print "Not yet implemented ! implement if required"
        return True

    @classmethod
    def validate_object(self, pure_json, ignore_extra_keys):
        if isinstance(pure_json, dict):
            pure_json = pure_json.copy()
            original_class_variables = []
            for attr in dir(self):
                if not str(attr).startswith("__") and getattr(self, str(attr)) == None:
                    original_class_variables.append(str(attr))
            pure_json_keys_set = set(pure_json.keys())
            original_class_variables_set = set(original_class_variables)

            extra_keys = pure_json_keys_set - original_class_variables_set
            keys_absent = original_class_variables_set - pure_json_keys_set
            if extra_keys and ignore_extra_keys == False:
                raise Exception("Extra keys {%s} in JSON " % (extra_keys))

            if keys_absent :
                self.validate_optional_fields(keys_absent=keys_absent)

            for key in pure_json.keys():
                clas = self.get_classes(key)
                if clas:
                    if isinstance(pure_json[key], dict):
                        clas.validate_object(pure_json[key], ignore_extra_keys)
                    elif isinstance(pure_json[key], list):
                        for item in pure_json[key]:
                            clas.validate_object(item, ignore_extra_keys)

    def assign_default_values(self):
        pass

    @classmethod
    def get_optional_fields(cls):
        return []

    @classmethod
    def validate_optional_fields(cls, keys_absent):
        optional_fields = cls.get_optional_fields()

        # all keys in keys_absent should be in optional_fields else throw exception

        for key in keys_absent:
            if key not in optional_fields:
                raise Exception('Required key : {%s} Missing' % key)
