from environs import Env

# Теперь используем вместо библиотеки python-dotenv библиотеку environs
env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")  # Забираем значение типа str
ADMINS = env.list("ADMINS")  # Тут у нас будет список из админов
IP = env.str("ip")  # Тоже str, но для айпи адреса хоста

USER = str(env.str("USER"))  # Берём юзера для входа в бд
PASS = str(env.str("PASS"))  # Берём пароль для входа
BASE = str(env.str("BASE"))  # Берём название базы для входа

QIWI_TOKEN = str(env.str("qiwi"))  # Киви токен
WALLET_QIWI = str(env.str("wallet"))  # Номер киви
QIWI_SECRET = str(env.str("qiwi_p_sec"))  # Приватный ключ


URL = f'postgresql+asyncpg://{USER}:{PASS}@{IP}/{BASE}'
