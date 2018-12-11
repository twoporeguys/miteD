import json
import datetime


def format_version_str(version):
    return version.replace('.', '_')


def get_members_if(check, instance):
    members = []
    for member in [getattr(instance, member_name) for member_name in dir(instance)]:
        if callable(member) and check(member):
            members.append(member)
    return members


class CustomJsonEncoder(json.JSONEncoder):
    """
    Our custom json encoder to handle datetime types
    """
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(self.DATE_TIME_FORMAT)
        return super(CustomJsonEncoder, self).default(obj)
