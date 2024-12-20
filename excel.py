import pandas as pd


FILE_PATH_data = "data.xlsx"
FILE_PATH_canditates = "candidates.xlsx"
FILE_PATH_closed = "closed_votings.xlsx"

def is_voting_closed(nomination):
    try:
        df_closed = pd.read_excel(FILE_PATH_closed)
        return nomination in df_closed["Номинация"].values and \
               df_closed.loc[df_closed["Номинация"] == nomination, "Статус"].iloc[0] == "Закрыто"
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Ошибка проверки статуса голосования: {e}")
        return False

def open_voting(nomination):
    try:
        df_closed = pd.read_excel(FILE_PATH_closed)

        if nomination not in df_closed["Номинация"].values:
            print(f"Номинация '{nomination}' отсутствует в таблице закрытых голосований.")
            return False

        df_closed.loc[df_closed["Номинация"] == nomination, "Статус"] = "Открыто"

        df_closed.to_excel(FILE_PATH_closed, index=False)
        print(f"Голосование за номинацию '{nomination}' открыто.")
        return True
    except FileNotFoundError:
        print("Файл закрытых голосований не найден.")
        return False
    except Exception as e:
        print(f"Ошибка изменения статуса голосования: {e}")
        return False


def reload_data():
    global df
    df = pd.read_excel(FILE_PATH_data)

def check_user(last_name, first_name, batchestvo, group):
    try:
        df = pd.read_excel(FILE_PATH_data)
        user_row = df[
            (df["Фамилия"].str.strip() == last_name.strip()) &
            (df["Имя"].str.strip() == first_name.strip()) &
            (df["Отчество"].str.strip() == batchestvo.strip()) &
            (df["Номер группы"].str.strip() == group.strip())
        ]

        if not user_row.empty:
            return user_row.iloc[0].to_dict()  
    except Exception as e:
        print(f"Ошибка проверки пользователя: {e}")
    return None


def save_vote(visitor_data, nomination, candidate):
    nomination = nomination.strip()
    candidate = candidate.strip()
    try:
        df = pd.read_excel(FILE_PATH_data)
        user_index = df[(df["Фамилия"].str.strip().str.lower() == visitor_data["surname"].strip().lower()) &
                (df["Имя"].str.strip().str.lower() == visitor_data["name"].strip().lower()) &
                (df["Отчество"].str.strip().str.lower() == visitor_data["batchestvo"].strip().lower()) &
                (df["Номер группы"].str.strip().str.lower() == visitor_data["group"].strip().lower())].index

        if user_index.empty:
            print("Пользователь не найден в базе данных.")
            print("Данные для поиска:", visitor_data)
            print("Данные из Excel:", df[["Фамилия", "Имя", "Отчество", "Номер группы"]].head())
            return False

        current_vote = df.loc[user_index[0], nomination]
        if pd.notna(current_vote) and str(current_vote).strip() != "0":
            print("Пользователь уже голосовал за эту номинацию.")
            return False 

        df.loc[user_index[0], nomination] = candidate
        df.to_excel(FILE_PATH_data, index=False)
        print(f"Голос за кандидата '{candidate}' в номинации '{nomination}' сохранён.")
        return True

    except Exception as e:
        print(f"Ошибка сохранения голоса: {e}")
        return False


def close_voting_for_nomination(nomination):
    nomination = nomination.strip()
    try:
        try:
            df_closed = pd.read_excel(FILE_PATH_closed)
        except FileNotFoundError:
            df_closed = pd.DataFrame(columns=["Номинация", "Статус"])

        if nomination in df_closed["Номинация"].values:
            df_closed.loc[df_closed["Номинация"] == nomination, "Статус"] = "Закрыто"
        else:
            new_row = {"Номинация": nomination, "Статус": "Закрыто"}
            df_closed = pd.concat([df_closed, pd.DataFrame([new_row])], ignore_index=True)

        df_closed.to_excel(FILE_PATH_closed, index=False)
    except Exception as e:
        print(f"Ошибка при закрытии голосования: {e}")

def get_nomination_candidates(nomination):
    try:
        df = pd.read_excel(FILE_PATH_canditates)
        candidates_row = df[df["Номинация"].str.strip() == nomination.strip()]
        if not candidates_row.empty:
            candidates = candidates_row.iloc[0].get("Кандидаты", "")
            if not candidates or pd.isna(candidates):
                print(f"Для номинации '{nomination}' не указаны кандидаты.")
                return []
            return [cand.strip() for cand in candidates.split(",") if cand.strip()]
        else:
            print(f"Номинация '{nomination}' не найдена в таблице.")
    except Exception as e:
        print(f"Ошибка получения кандидатов для номинации '{nomination}': {e}")
    return []


def change_status(last_name, first_name, batchestvo, group):
    try:
        df = pd.read_excel(FILE_PATH_data)

        df["Фамилия"] = df["Фамилия"].str.strip()
        df["Имя"] = df["Имя"].str.strip()
        df["Номер группы"] = df["Номер группы"].str.strip()
        df["Отчество"] = df["Отчество"].str.strip()

        user_index = df[(df["Фамилия"] == last_name.strip()) &
                        (df["Имя"] == first_name.strip()) &
                        (df["Отчество"] == batchestvo.strip()) &
                        (df["Номер группы"] == group.strip())].index

        if user_index.empty:
            print("Пользователь не найден")
            return False

        df.loc[user_index, "Авторизован"] = 1

        df.to_excel(FILE_PATH_data, index=False)
        print(f"Статус пользователя {last_name} {first_name} обновлён на '1'.")
        return True
    except Exception as e:
        print(f"Ошибка изменения статуса: {e}")
        return False

