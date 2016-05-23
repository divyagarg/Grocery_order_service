import datetime


def json_serial(obj):
	if isinstance(obj, datetime.datetime):
		serial = obj.isoformat()
		return serial
	raise TypeError("Type not serializable")
