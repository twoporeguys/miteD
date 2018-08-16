def format_version_str(version):
    return version.replace('.', '_')


def get_members_if(check, instance):
    members = []
    for member in [getattr(instance, member_name) for member_name in dir(instance)]:
        if callable(member) and check(member):
            members.append(member)
    return members
