USER_FILE = "users.txt"

def add_user(user_id):
    try:
        with open(USER_FILE, "a") as f:
            f.write(f"{user_id}\n")
    except Exception as e:
        print(f"Ошибка добавления пользователя: {e}")

def get_all_users():
    try:
        with open(USER_FILE, "r") as f:
            return list(set(int(line.strip()) for line in f if line.strip().isdigit()))
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return []
    
