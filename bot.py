from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from config import BOT_TOKEN, ADMINS
from excel import check_user, save_vote, get_nomination_candidates, change_status, reload_data, is_voting_closed, close_voting_for_nomination, open_voting
from utils import add_user, get_all_users
from dataclasses import asdict, dataclass
import asyncio


@dataclass
class Visitor:
    user_id: str
    surname: str
    name: str
    batchestvo: str
    group: str
    top_creative: str
    top_curators: str
    top_freshman: str
    top_group: str
    top_headman: str
    top_it_person: str
    top_project: str


storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

active_sessions = {}
active_nominations = {}
nominations = ["TOP GROUP", "TOP CURATORS", "TOP FRESHMAN", "TOP HEADMAN", "TOP PROJECT", "TOP CREATIVE PERSON", "TOP IT PERSON"]
list_vote = []



@dp.message_handler(commands=["start"])
async def command_start(message: types.Message):
    await message.answer("Добрый вечер, дамы и господа! 🌟\n\n"
                         "С радостью приветствую вас на долгожданном и захватывающем проекте TOP HSCM&S!\n\n"
                         "Вас будет ждать много всего интересного и увлекательного. Каждый из вас сможет не только "
                         "ознакомиться с участниками, но и принять активное участие в процессе голосования. "
                         "И это будет вашим шансом подарить заслуженные овации тем, кто действительно shines!\n\n"
                         "Пусть каждый из вас станет частью этого грандиозного события, ведь сегодня мы не просто "
                         "выбираем, а отмечаем таланты, стремления и достижения.\n\n"
                         "Пусть сегодня сияют все! ✨ Готовы? Начинаем!")
    await message.answer("Давайте начнём! Введите /login для дальнейшей работы")


@dp.message_handler(commands=["help"])
async def command_help(message: types.Message):
    await message.answer(
        "Доступные команды:\n/start - Начало работы бота\n/login - Регистрация"
        "\n/show_vote - Показ всех доступных номинаций для голосования\n/vote - Голосование"
        "\n/contacts - Создатели бота"
        "\n/me - Показ Ваших голосов за все номинации"
        "\n\nЕсли возникли какие-то трудности или были обнаружены ошибки в боте, то "
        "сообщите об этом @frlsua (Лера Семенова). Спасибо!"
        
    )

@dataclass
class form(StatesGroup):
    wait_message = State()

@dp.message_handler(commands=["login"])
async def command_login(message: types.Message):
    await message.answer("Введите следующую информацию в одном сообщении:\n"
                         "Фамилия Имя Отчество Полный(!) номер группы\n\n"
                         "Пример:"
                         "Семенова Валерия Олеговна 15.27Д-МО01/23б")
    await form.wait_message.set()

@dp.message_handler(state=form.wait_message)
async def login_info(message: types.Message, state: FSMContext):
    info = message.text

    if len(info.split(" ")) != 4:
        await message.answer("Неправильный ввод. Попробуйте ещё раз\nВведите /login)")
        return
    if len(info.split(" ")) == 4:
        surname, name, batchestvo, group = info.split(" ")
        if check_user(surname, name, batchestvo, group):
            vis = Visitor(
                user_id=message.from_user.id,
                surname=surname,
                name=name,
                batchestvo=batchestvo,
                group=group,
                top_creative="",
                top_curators="",
                top_freshman="",
                top_group="",
                top_headman="",
                top_it_person="",
                top_project=""
            )
            list_vote.append(vis)
            active_sessions[message.from_user.id] = vis
            change_status(surname, name, batchestvo, group)
            add_user(message.from_user.id)
            await message.answer("Вы успешно авторизованы!")
        else:
            await message.answer("Вы не значитесь в списке гостей! Проверьте данные.")
    await state.finish()


@dp.message_handler(commands=["contacts"])
async def process_contacts_command(message: types.Message):
    await message.answer(
        "Бот был разработан в рамках проекта IT-клуба - https://vk.com/err.itclub"
        "\n\nРазработчики:\nФакова Настя - @monresu\nСеменова Валерия - @frlsua"
    )


@dp.message_handler(commands=["show_vote"])
async def process_show_vote_command(message: types.Message):
    if len(active_nominations) == 0:
        await message.answer("К сожалению, голосование ещё не открыто")
    else:
        txt = "Номинации открытые для голосования: \n"
        i = 1
        for nomination in active_nominations:
            txt += f"{i}. {nomination}\n"
        await message.answer(txt)

async def vote_filter(message: types.Message) -> bool:
    if not message.text.startswith('/vote'):
        return False
    if message.text.strip() == '/vote':
        await message.answer("Вы не указали номинацию. Попробуйте ещё раз")
        return False
    command = message.text[:5]
    nomination = message.text[6:].upper()
    if nomination not in nominations:
        await message.answer("Такой номинации нет. Всего 7 номинаций:\n"
                             "\n1. TOP GROUP\n2. TOP CURATORS\n3. TOP HEADMAN\n4. TOP FRESHMAN\n5. TOP CREATIVE PERSON"
                             "\n6. TOP PROJECT\n7. TOP IT PERSON"
                             "\n\nПопробуйте ещё раз")
        return False
    if nomination in nominations and nomination not in active_nominations:
        await message.answer("Данная номинация ещё не открыта для голосования. Попробуйте сделать это позже")
        return False
    return True

@dp.message_handler(vote_filter)
async def vote_cool(message: types.Message):
    nomination = message.text[6:].upper()
    candidates = get_nomination_candidates(nomination)

    keyboard = InlineKeyboardMarkup()
    for candidate in candidates:
        keyboard.add(InlineKeyboardButton(text=candidate, callback_data=f"vote_{nomination}_{candidate}"))

    text = f"🗳 Открыто голосование за номинацию: *{nomination}*\n\nКандидаты:\n"
    for i, candidate in enumerate(candidates, start=1):
        text += f"{i}. {candidate}\n"
    text += "\nПожалуйста, выберите кандидата, нажав на кнопку ниже"

    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message_handler(vote_filter)
async def vote_cool(message: types.Message):
    user_id = message.from_user.id

    visitor = active_sessions.get(user_id)
    if not visitor:
        await message.reply("Вы не авторизованы. Введите /login для начала.")
        return

    nomination = message.text[6:].upper()
    candidates = get_nomination_candidates(nomination)

    if not candidates:
        await message.reply(f"Кандидаты для номинации '{nomination}' не найдены.")
        return

    user_vote = getattr(visitor, f"top_{nomination.lower()}", None)
    if user_vote:
        await message.reply(
            f"Вы уже голосовали за номинацию '{nomination}'. Ваш выбор: '{user_vote}'.",
            parse_mode="Markdown"
        )
        return

    keyboard = InlineKeyboardMarkup()
    for candidate in candidates:
        keyboard.add(InlineKeyboardButton(text=candidate, callback_data=f"vote_{nomination}_{candidate}"))

    text = f"🗳 Открыто голосование за номинацию: *{nomination}*\n\nКандидаты:\n"
    for i, candidate in enumerate(candidates, start=1):
        text += f"{i}. {candidate}\n"
    text += "\nПожалуйста, выберите кандидата, нажав на кнопку ниже."

    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard, parse_mode="Markdown")



@dp.message_handler(commands=["open_vote"])
async def open_vote(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номинацию. Возможные номинации:"
                            "\n/open_vote TOP GROUP"
                            "\n/open_vote TOP CURATORS"
                            "\n/open_vote TOP HEADMAN"
                            "\n/open_vote TOP FRESHMAN"
                            "\n/open_vote TOP PROJECT"
                            "\n/open_vote TOP CREATIVE PERSON"
                            "\n/open_vote TOP IT PERSON")
        return

    nomination = args[1].strip()
    candidates = get_nomination_candidates(nomination)

    if is_voting_closed(nomination):
        open_voting(nomination)

    if not candidates:
        await message.reply(f"Кандидаты для номинации '{nomination}' не найдены.")
        return

    active_nominations[nomination] = candidates

    async with state.proxy() as data:
        data["nomination"] = nomination
        data["candidates"] = candidates
        print(data, '123')

    text = f"🗳 Открыто голосование за номинацию: *{nomination}*\n\nКандидаты:\n"
    for i, candidate in enumerate(candidates, start=1):
        text += f"{i}. {candidate}\n"
    text += "\nПожалуйста, выберите кандидата, нажав на кнопку ниже."

    keyboard = InlineKeyboardMarkup()
    for candidate in candidates:
        keyboard.add(InlineKeyboardButton(text=candidate, callback_data=f"vote_{nomination}_{candidate}"))

    users = get_all_users()
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await message.reply(f"Голосование за номинацию '{nomination}' началось!")


@dp.message_handler(commands=["close_vote"])
async def close_vote(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Укажите номинацию. Пример: /close_vote Староста")
        return

    nomination = args[1].strip()

    candidates = get_nomination_candidates(nomination)
    if not candidates:
        await message.reply(f"Номинация '{nomination}' не найдена.")
        return

    close_voting_for_nomination(nomination)
    
    del active_nominations[f'{nomination}']
    users = get_all_users()
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"⚠️ Голосование за номинацию '{nomination}' завершено. Спасибо за участие!"
            )
        except Exception as e:
            print(f"Не удалось уведомить пользователя {user_id}: {e}")

    await message.reply(f"Голосование за номинацию '{nomination}' закрыто!")


@dp.callback_query_handler(lambda call: call.data.startswith("vote_"))
async def process_vote(call: types.CallbackQuery):
    user_id = call.from_user.id

    

    visitor = active_sessions.get(user_id)
    if not visitor:
        await call.answer("Вы не авторизованы. Введите /start для начала.", show_alert=True)
        return

    _, nomination, candidate = call.data.split("_", 2)

    if is_voting_closed(nomination):
        await call.answer(f"Голосование за номинацию '{nomination}' уже завершено. Вы опоздали!", show_alert=True)
        return

    if nomination not in active_nominations:
        await call.answer("Голосование ещё не началось или завершено.", show_alert=True)
        return

    if candidate not in active_nominations[nomination]:
        await call.answer("Неверный выбор кандидата.", show_alert=True)
        return
    
    list_vote.append([nomination, candidate])


    if save_vote(asdict(visitor), nomination, candidate):
        setattr(visitor, f"top_{nomination.lower()}", candidate)  
        await call.message.reply(f"Ваш голос за кандидата '{candidate}' в номинации '{nomination}' принят!")
        await call.answer("Ваш голос принят!")
    else:
        await call.answer(f"Вы уже голосовали за номинацию '{nomination}'.", show_alert=True)

    

@dp.message_handler(commands=["me"])
async def show_votes(message: types.Message):
    user_id = message.from_user.id
    visitor = active_sessions.get(user_id)

    if not visitor:
        await message.reply("Вы не авторизованы. Введите /start для начала.")
        return

    reload_data()  
    user_data = check_user(visitor.surname, visitor.name, visitor.batchestvo, visitor.group)

    if not user_data:
        await message.reply("Ваши данные не найдены в системе.")
        return

    response = f"👤 **Голосующий:** {visitor.surname} {visitor.name} {visitor.batchestvo}, группа {visitor.group}\n\n"
    response += "📋 **Голоса в номинациях:**\n"

    for column in user_data.keys():
        if column not in ["Фамилия", "Имя", "Отчество", "Номер группы", "Авторизован"]:
            vote = str(user_data[column]).strip()
            print(vote)
            response += f"- {column}: {vote if vote!='0' and vote!=0 else 'Голосования ещё не было либо же вы опоздали'}\n"

    await message.reply(response, parse_mode="Markdown")

@dp.message_handler(commands=["end"])
async def end_event(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав для использования этой команды.")
        return

    users = get_all_users()
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🎉 Мероприятие окончено! Спасибо за участие! 🙏\n\n\n\nP.S. Пропишите команду /contacts"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await message.reply("Уведомление всем пользователям успешно отправлено! Бот завершает работу.")

    await bot.session.close()  
    asyncio.get_event_loop().stop() 

@dp.message_handler(commands=["sendsend"])
async def send(message: types.Message):
    users = get_all_users()
    for user_id in set(users):
        try:
            await bot.send_message(chat_id=user_id, text=
                "Пожалуйста! Пропишите /start снова."
            ) 
        except Exception as e:
            print(f"Не удалось уведомить пользователя {user_id}: {e}")

@dp.message_handler(lambda message: message.text and message.text.lower() == "топ")
async def top(message: types.Message):
    await message.reply("Настя топ айти персон")


@dp.message_handler()
async def any_message(message: types.Message):
    await message.answer("К сожалению, бот не может обработать подобную информацию :(\n\n"
                         "Если хочешь проголосовать, то напиши /vote *номинация*\n\n"
                         "Всего 7 номинаций:\n"
                         "\n1. TOP GROUP\n2. TOP CURATORS\n3. TOP HEADMAN\n4. TOP FRESHMAN\n5. TOP CREATIVE PERSON"
                         "\n6. TOP PROJECT\n7. TOP IT PERSON")
    



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

