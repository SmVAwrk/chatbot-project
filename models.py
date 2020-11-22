
from pony.orm import Database, Required, Json

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя во время сценария."""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class UserRequest(db.Entity):
    """Данные о заявках пользователей."""
    user_id = Required(str)
    name = Required(str)
    email = Required(str)


db.generate_mapping(create_tables=True)

