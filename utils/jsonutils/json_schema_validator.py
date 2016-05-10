from apps.app_v1.api import RequiredFieldMissing, error_code

__author__ = 'divyagarg'
import collections


FUNCTIONS = 'functions'
SCHEMA = 'schema'
REQUIRED = 'required'


def Integer(val, min_value=None, max_value=None):
    try:
        int(val)
    except Exception as e:
        raise Exception('Not an valid Integer : {%s}'%val)
    if min_value:
        if int(val) < min_value:
            raise Exception('Minimum value cannot be lessed than :{%s} , provided value :{%s}'%(min_value, val))
    if max_value:
        if int(val) > max_value:
            raise Exception('Maximum value cannot be exceed than :{%s} , provided value :{%s}'%(max_value, val))


def String(val, min_length=None, max_length=None):
    if not isinstance(val, (unicode, str)):
        raise Exception('Not an valid String : {%s}' % val)
    if min_length:
        if len(val) < min_length:
            raise Exception('Minimum length of :{%s} has to be :{%s}'%(val, min_length))
    if max_length:
        if len(val) > max_length:
            raise Exception('Maximum length of :{%s} has to be :{%s}'%(val, min_length))

def Contained(val, contained_in=None, not_contained_in=None):
    if contained_in is not None:
        try:
            val = int(val)
        except ValueError:
            val = val.upper()

        if val not in contained_in:
            raise Exception('Value : {%s} has to be present in : {%s}'%(val, contained_in))

    if not_contained_in is not None:
        try:
            val = int(val)
        except ValueError:
            val=val.upper()

        if val in not_contained_in:
            raise Exception('Value : {%s} should not be present in : {%s}'%(val, contained_in))

def Float(val, min_value=None, max_value=None):
    try:
        float(val)
    except Exception as e:
        raise Exception('Not an valid Float : {%s}'%val)
    if min_value:
        if float(val) < min_value:
            raise Exception('Minimum value cannot be lessed than :{%s} , provided value :{%s}'%(min_value, val))
    if max_value:
        if float(val) > max_value:
            raise Exception('Maximum value cannot be exceed than :{%s} , provided value :{%s}'%(max_value, val))



def Dictionary(val):
    if not isinstance(val, dict):
        raise Exception('Value : {%s} is not an valid Json'%(val))



def List(val, min_length=None, max_length=None):
    if not isinstance(val, list):
        raise Exception('Not an valid List : {%s}' % val)

    if min_length:
        if len(val) < min_length:
            raise Exception('Minimum length of :{%s} has to be : {%s}' % (val, min_length))

    if max_length:
        if len(val) > max_length:
            raise Exception('Maximum length of :{%s} has to be : {%s}' % (val, min_length))


def Pincode(val):
    try:
        if str(int(val)).__len__() != 6:
            raise Exception('Not an valid Pincode : {%s}'%val)
    except Exception as e:
        raise Exception('Not an valid Pincode : {%s}'%val)


def MobileNumber(val):
    try:
        if str(int(val)).__len__()!=10:
            raise Exception('Not an Valid Mobile number : {%s} '%val)

        if len(val)==10 and not val[0]=="0":
            pass
        elif len(val)==11 and val[0]=="0" and val[1]!="0":
            pass
        else:
            raise Exception('Not an Valid Mobile number : {%s} '%val)
    except Exception as e:
        raise Exception('Not an Valid Mobile number : {%s} '%val)



def validate(data, schema):
    for key, validator_json in schema.items():
        required = validator_json.get(REQUIRED, True)
        if required and key not in data:
            raise RequiredFieldMissing(code = error_code['data_missing'], message = 'key missing is :{%s}'%key)
        if key in data:
            value = data[key]
            if FUNCTIONS in validator_json:
                for function in validator_json[FUNCTIONS]:
                    for func_name, kwargs in function.items():
                        func_name(val=value, **kwargs)
            if SCHEMA in validator_json:
                schema = validator_json[SCHEMA]
                if isinstance(value, collections.Iterable) and not isinstance(value, dict):
                    for nested_json in value:
                        validate(data=nested_json, schema=schema)
                if isinstance(value, dict):
                    validate(data=value, schema=schema)

