from client import client

user_cache = {}


def populate_cache():
    global user_cache
    response = client.users_list()
    if not response["ok"]:
        raise "shit"

    user_cache = {user["id"]: user
                  for user in response["members"]}


def resolve_user(user_id):
    global user_cache
    if not user_id in user_cache:
        response = client.users_info(user=user_id)
        if not response["ok"]:
            raise "shit"

        user_cache[user_id] = response["user"]
        return response["user"]

    return user_cache[user_id]


def start_im(user_id):
    response = client.im_open(user=user_id)
    if not response["ok"]:
        raise "shit"

    return response["channel"]["id"]


def get_conversations():
    response = client.users_conversations()

    if not response["ok"]:
        raise "shit"

    return response["channels"]


def _user_validator(u):
    return (not u["deleted"]
            and not u["is_bot"]
            and not u["is_restricted"]
            and not u["name"] == "slackbot")


def get_slack_users(channel):
    response = client.conversations_members(channel=channel)
    if not response["ok"]:
        raise "shit"

    user_ids = map(resolve_user, response["members"])

    return filter(_user_validator, user_ids)
