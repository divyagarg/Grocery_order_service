from apps.app_v1.api import NoSuchStatusException
from apps.app_v1.models.models import Status
from apps.app_v1.api import ERROR

__author__ = 'divyagarg'


class StatusService(object):
	@staticmethod
	def get_status_id(value):
		status = Status.query.filter_by(status_code=value).first()
		if status is None:
			raise NoSuchStatusException(ERROR.INVALID_STATUS)
		return status.id

	@staticmethod
	def get_status_code(status_id):
		status = Status.query.filter_by(id=status_id).first()
		if status is None:
			raise NoSuchStatusException(ERROR.INVALID_STATUS)
		return status.status_code
