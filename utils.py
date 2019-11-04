import datetime


def create_mention(user_id):
    return f"<@{user_id}>"


def create_mentions(user_ids):
    users = list(map(create_mention, user_ids))
    if len(users) == 1:
        return users[0]
    if len(users) == 2:
        return f"{users[0]} og {users[1]}"
    return f"{', '.join(users[:-1])} og {users[-1]}"


def sane_time(dt):
    return dt.strftime('%d/%m %H:%M')


def timedelta_to_seconds(td):
    return td.total_seconds()


def seconds_to_timedelta(seconds):
    return datetime.timedelta(seconds=seconds)
