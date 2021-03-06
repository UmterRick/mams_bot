from config import *
from database import *
from parser_file import *
from keyboards import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
memory_storage = MemoryStorage()
dp = Dispatcher(bot, storage=memory_storage)


HTML = get_html(C_URL)
temp_course_text = {}


class MainStates(StatesGroup):
    check_state = State()
    show_contact = State()
    show_my_courses = State()
    choose_trainer = State()
    wait_menu_click = State()
    wait_for_category = State()
    wait_for_course = State()
    wait_for_group = State()
    wait_for_client_answer = State()
    students_list = State()
    check = State()


class EnterStates(StatesGroup):
    login_state = State()
    password_state = State()



class AdminStates(StatesGroup):
    answer_enroll = State()
    add_group_time = State()
    add_group_days = State()
    add_group_flag = State()
    add_note = State()


def create_callback_data(arg1, arg2):
    return ";".join([arg1, arg2])


def separate_callback_data(data):
    return data.split(";")


async def StateName(state: FSMContext):
    cur_state = await state.get_state()
    return cur_state


@dp.message_handler(commands='start', state='*')  # STEP 1
async def auth_user_type(message: types.Message, state: FSMContext):
    global CHAT_ID, coursesId, USER_TYPE
    db_create_tables(DB_NAME)
    get_topics(HTML)
    coursesId = get_content(HTML)
    CHAT_ID = message.chat.id
    users = db_read_users(DB_NAME)
    registered = []
    for user in users:
        registered.append(int(user[1]))

    print('redistered id = ', registered)
    if str(message.chat.id).startswith('-'):
        await bot.send_message(CHAT_ID, admin_groups_start)

        USER_TYPE = 'Адміністратор📒'
        await EnterStates.password_state.set()
        cur_state = await state.get_state()

        if message.from_user.last_name is not None:
            user_name = ' '.join([str(message.chat.first_name), str(message.chat.last_name)])
        else:
            user_name = ' '.join([str(message.chat.first_name)])
        nickname = message.chat.username
        chat_info = [message.chat.id, user_name, nickname, str(cur_state)]
        db_start_add_user(DB_NAME, chat_info)

        db_save_var(DB_NAME, CHAT_ID, 'user_type', 'admin_group')
    elif CHAT_ID in registered:
        greeting_info = db_get_user_info(DB_NAME, CHAT_ID)
        greeting_info = greeting_info[0]
        print('greeting = ', greeting_info)
        type_ = 'non_type'
        name = 'no_name'
        if greeting_info[2] == 'admin':
            type_ = '<b>Адміністратор</b>'
            name = greeting_info[0]
        elif greeting_info[2] == 'client':
            type_ = '<b>Учень</b>'
            name = greeting_info[0]
        elif greeting_info[2] == 'admin_group':
            type_ = '<b>група Адміністраторів</b>'
            name = ''
        elif greeting_info[2] == 'trainer':
            type_ = '<b>тренер</b>'
            name = ''
        await message.answer(f"Привіт ми вже знайомі, ви {type_} <i>{name}</i>"
                             f" в нашому освітньому центрі \n <b> 📜 Головне Меню 📜 </b> ",
                             parse_mode='HTML', reply_markup=MenuKB(CHAT_ID))
        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)
    else:
        await EnterStates.login_state.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

        cur_state = await state.get_state()
        if message.from_user.last_name is not None:
            user_name = ' '.join([str(message.from_user.first_name), str(message.from_user.last_name)])
        else:
            user_name = ' '.join([str(message.from_user.first_name)])
        nickname = message.from_user.username

        user_info = [message.from_user.id, user_name, nickname, str(cur_state)]
        db_start_add_user(DB_NAME, user_info)

        commands = [types.BotCommand(command="/start", description="Начало работы с ботом"), ]
        await bot.set_my_commands(commands)

        await message.answer(start_text, reply_markup=UserTypeKB())
        del user_name, nickname, user_info


@dp.callback_query_handler(state=EnterStates.login_state)
async def auth_step_two(call: types.CallbackQuery, state: FSMContext):
    global USER_TYPE
    print('auth_step_two data = ', call.data)

    USER_TYPE = call.data
    await state.update_data(userType=call.data, userID=call.from_user.id)

    if USER_TYPE == 'Адміністратор📒':
        await call.message.edit_text('Для входу як адміністратор потрібен пароль!\nВведіть пароль: ')
        await EnterStates.password_state.set()

    elif USER_TYPE == 'Учень🤓':
        await call.message.edit_text(f'Ви увійшли як {call.data}', reply_markup=MenuKB(call.from_user.id))
        db_save_var(DB_NAME, call.from_user.id, 'user_type', 'client')

        await MainStates.wait_menu_click.set()

    elif USER_TYPE == 'Тренер📝':
        await call.message.edit_text('Для входу як тренер потрібен пароль!\nВведіть пароль: ')
        await EnterStates.password_state.set()
    else:
        await call.message.edit_text('Оберіть коректний тип користувача!')
        return

    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.message_handler(state=EnterStates.password_state)  # 2.3  PASSWORD VALID
async def check_password(message: types.Message, state: FSMContext):
    print('check_password data = ', message.text)
    if message.text == ADMIN_PASSWORD and str(message.chat.id).startswith('-'):
        await bot.send_message(CHAT_ID, f'Бот активований у групі адміністраторів')

        await MainStates.wait_menu_click.set()
    elif USER_TYPE == 'Адміністратор📒' and message.text == ADMIN_PASSWORD:
        await bot.send_message(CHAT_ID, 'Ви увійшли як <b>Адміністратор</b>', parse_mode='HTML',
                               reply_markup=MenuKB(message.chat.id))
        db_save_var(DB_NAME, message.chat.id, 'user_type', 'admin')
        await MainStates.wait_menu_click.set()
    elif USER_TYPE == 'Тренер📝' and message.text == TRAINER_PASSWORD:
        await bot.send_message(CHAT_ID, 'Оберіть себе у списку', parse_mode='HTML', reply_markup=TrainersKB(DB_NAME))
        db_save_var(DB_NAME, message.chat.id, 'user_type', 'trainer')

        await MainStates.choose_trainer.set()

    else:
        await message.answer('Невірний пароль, спробуйте ще раз!')
        return
    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, message.chat.id, user_state)


@dp.callback_query_handler(state=MainStates.choose_trainer)
async def trainer_name_clicked(call: types.CallbackQuery, state: FSMContext):
    print('trainer_name_clicked data = ', call.data)  # ([],[()])

    if call.data == 'turn_back':
        await call.message.edit_text(start_text, 'HTML', reply_markup=UserTypeKB())
        await EnterStates.login_state.set()
    else:
        db_save_var(DB_NAME, call.from_user.id, 'group_id', call.data)
        await call.message.edit_text('<b> 📜 Головне Меню 📜 </b> ', parse_mode='HTML', reply_markup=MenuKB(CHAT_ID))
        await MainStates.wait_menu_click.set()
    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(state=MainStates.wait_menu_click)
async def menu_btn_clicked(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID
    print('menu_btn_clicked data = ', call.data)

    CHAT_ID = call.from_user.id
    if str(call.message.chat.id)[0] == '-':
        print('check_client_enroll data = ', call.data)
        data = call.data
        enroll_id = data[0:data.find('T')]
        telegram_id = data[data.find(':') + 1:data.find(';')]
        group_info, course_name, to_course_id = db_get_group_info(DB_NAME, enroll_id)
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton('OK', callback_data='enroll_ok')
        keyboard.row(back_btn)
        if ';accept' in call.data:
            db_accept_enroll(DB_NAME, telegram_id, int(enroll_id))
            client_enroll_answer = f'Ваш запит на зачислення до курсу: \n▶️ {course_name}\nДо групи\n▶️ {group_info} ' \
                                   f'\n\n <b>✅ПРИЙНЯТО✅</b>'
            await call.message.delete()
            await bot.send_message(telegram_id, client_enroll_answer, 'HTML', reply_markup=keyboard)
        elif ';cancel_enroll' in call.data:
            db_delete_enroll(DB_NAME, telegram_id, int(enroll_id))
            client_enroll_answer = f'Ваш запит на зачислення до курсу: \n▶️ {course_name}\nДо групи\n▶️ {group_info} ' \
                                   f"\n\n<b>❎ВІДХИЛЕНО❎</b>" \
                                   f"\nЯкщо, у вас є запитання обреіть зручний вам спосіб зв'язку із нами у 'Контактах'"

            await call.message.delete()
            await bot.send_message(telegram_id, client_enroll_answer, 'HTML', reply_markup=keyboard)
        elif call.data == 'enroll_ok':
            await call.message.delete()
        else:
            print('answer_enroll catch callback = ', call.data)

    if call.data == 'all_courses':
        await call.message.edit_text('Оберіть категорію курсів:', reply_markup=TopicKB())
        await MainStates.wait_for_category.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    if call.data == 'my_course' or call.data == 'trainer_course':
        await call.message.edit_text('Ваші курси:', reply_markup=MyCoursesKB(DB_NAME, call.from_user.id))

        await MainStates.show_my_courses.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    if call.data == 'contacts':
        await call.message.edit_text('Наші контакти :', reply_markup=ContactKB())

        await MainStates.show_contact.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    if call.data == 'turn_back':
        await EnterStates.login_state.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)
        await call.message.edit_text(start_text, reply_markup=UserTypeKB())

    if call.data == 'enroll_ok':
        await call.message.delete()


@dp.callback_query_handler(state=[MainStates.show_contact, MainStates.show_my_courses])
async def show_contacts(call: types.CallbackQuery, state: FSMContext):
    print('show_contacts data = ', call.data)

    if call.data == 'turn_back':
        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

        await call.message.edit_text('<b> 📜 Головне Меню 📜 </b> ', parse_mode='HTML',
                                     reply_markup=MenuKB(call.from_user.id))
    if call.data == 'phone1':
        await bot.answer_callback_query(call.id, '+38(097)-270-50-72', True)
    elif call.data == 'phone2':
        await bot.answer_callback_query(call.id, '+38(050)-270-50-72', True)

    user_info = db_get_user_info(DB_NAME, call.from_user.id)
    print('type = ', user_info[0][2])
    print(';my_groups' in call.data, user_info[0][2] == 'trainer')
    if ';my_group' in call.data and user_info[0][2] == 'trainer':
        group_id = call.data[:call.data.find(';')]
        print('my_groups', group_id)
        keyboard = InlineKeyboardMarkup()
        students = db_get_group_students(DB_NAME, int(group_id))
        for student in students:
            user_btn = InlineKeyboardButton(student[1], callback_data=group_id + ';T_ID:' + str(student[0]))
            keyboard.row(user_btn)
        back_btn = InlineKeyboardButton('⬅️ Назад', callback_data=group_id + ';stud_back')
        keyboard.row(back_btn)
        await call.message.edit_text('Список студентів до групи :', reply_markup=keyboard)

        await MainStates.students_list.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(lambda c: c.data in range_to_str_list(get_topics(HTML)) or c.data == 'turn_back',
                           state=MainStates.wait_for_category)
async def send_courses(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID, temp_course_text
    print('send_courses data = ', call.data)
    CHAT_ID = call.from_user.id
    Topics = db_read_topics(DB_NAME)
    if call.data == 'turn_back':

        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

        await call.message.edit_text('<b> 📜 Головне Меню 📜 </b> ', parse_mode='HTML',
                                     reply_markup=MenuKB(call.from_user.id))
    else:
        category = int(call.data)
        save_to = 'viewing_category'
        db_save_var(DB_NAME, CHAT_ID, save_to, category)

        if category in Topics.keys():
            await CoursesKB(call, category, state, temp_course_text)

            await MainStates.wait_for_course.set()
            user_state = await StateName(state)
            db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(state=MainStates.wait_for_course)
async def catch_group(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID, msgID, USER_TYPE
    print('catch_group data = ', call.data)
    CHAT_ID = call.from_user.id
    state_data = await state.get_data()
    if call.data == 'turn_back':

        await MainStates.wait_for_category.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

        state_data = await state.get_data()

        if 'msgToDel' not in state_data.keys():
            var = db_get_save_var(DB_NAME, call.from_user.id, 'temp_var')
            var = str_to_list(var)
            await state.update_data(msgToDel=var)
            state_data = await state.get_data()

        if call.message.message_id in state_data['msgToDel']:
            state_data['msgToDel'].remove(call.message.message_id)
            for delMsg in state_data['msgToDel']:
                await bot.delete_message(CHAT_ID, delMsg)
        else:
            print(f'Warning : {call.message.message_id} not in list')
        await call.message.edit_text('Оберіть категорію курсів:', reply_markup=TopicKB())
        return

    if not 'msgToDel' in state_data:
        var = db_get_save_var(DB_NAME, call.from_user.id, 'temp_var')
        var = str_to_list(var)
        await state.update_data(msgToDel=var)
        state_data = await state.get_data()

    state_data['msgToDel'].remove(call.message.message_id)
    for delMsg in state_data['msgToDel']:
        await bot.delete_message(CHAT_ID, delMsg)

    cur_groups = db_read_groups(DB_NAME, call.data)
    await state.update_data(curCourse=call.data)

    keyboard = await GroupsKB(cur_groups, call.from_user.id, call.data, state)
    temp_text = call.message.text
    await call.message.edit_text(temp_text, reply_markup=keyboard)

    await MainStates.wait_for_group.set()
    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, call.from_user.id, user_state)


@dp.callback_query_handler(lambda c: 'accept' not in c.data, state=MainStates.wait_for_group)
async def admin_group(call: types.CallbackQuery, state: FSMContext):
    global msgID, CHAT_ID
    print('admin_group data = ', call.data, '  ', call.message.chat.id)
    msgID = call.message.message_id
    CHAT_ID = call.from_user.id
    group_id = call.data[0:call.data.find(';')]
    group_info, course_info, to_course_id = db_get_group_info(DB_NAME, group_id)
    if 'edit' in call.data:
        await state.update_data(editing=True)

    if 'add_group' in call.data or ';edit' in call.data:  # ADMIN CHOOSE GROUP TIME
        flag_keyboard = InlineKeyboardMarkup()

        online_btn = InlineKeyboardButton(text='Онлайн', callback_data='0')
        offline_btn = InlineKeyboardButton(text='Офлайн', callback_data='1')
        flag_keyboard.add(online_btn)
        flag_keyboard.add(offline_btn)

        await call.message.edit_text('Оберіть тип групи:', reply_markup=flag_keyboard)
        await state.update_data(group_id=group_id, group_flag=None, group_time=None, group_day=None, group_datetime=[])

        await AdminStates.add_group_flag.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif ';del' in call.data:
        db_delete_group(DB_NAME, group_id)
        cur_groups = db_read_groups(DB_NAME, to_course_id)
        keyboard = await GroupsKB(cur_groups, call.from_user.id, to_course_id, state)

        await call.message.edit_text(text=f'Видалено групу:', reply_markup=keyboard)

        await MainStates.wait_for_group.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, call.from_user.id, user_state)

    elif ';enroll' in call.data:
        phone_number = db_get_save_var(DB_NAME, call.from_user.id, 'contacts')  # test print
        print(phone_number)
        if phone_number == 'empty_number':
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            ok_btn = types.KeyboardButton('Так', request_contact=True)
            no_btn = types.KeyboardButton('Ні')
            keyboard.add(ok_btn, no_btn)

        else:
            keyboard = InlineKeyboardMarkup()
            ok_btn = InlineKeyboardButton('Так', request_contact=True, callback_data='enroll_accept')
            no_btn = InlineKeyboardButton('Ні', callback_data='enroll_cancel')
            keyboard.row(ok_btn, no_btn)
        await call.message.delete()
        accept_enroll = await bot.send_message(chat_id=CHAT_ID,
                                               text=f'Подати завку до групи:\n<b>📅(🕒) {group_info}</b>\nДо курсу:\n<i>{course_info}</i>',
                                               reply_markup=keyboard, parse_mode='HTML')
        db_save_var(DB_NAME, call.from_user.id, 'temp_var', accept_enroll.message_id)
        user_info = db_get_user_info(DB_NAME, call.from_user.id)

        db_save_var(DB_NAME, CHAT_ID, 'temp_var', accept_enroll.message_id)
        new_enrolls = user_info[3]
        print('admin_group new_enrolls = ', new_enrolls)
        if len(new_enrolls) == 0:
            new_enrolls = [int(group_id)]
            print('save this enroll to db1: ', new_enrolls, type(new_enrolls))
            db_save_var(DB_NAME, CHAT_ID, 'enroll', str(new_enrolls))

            await MainStates.wait_for_client_answer.set()

        elif int(group_id) not in new_enrolls:
            new_enrolls.append(int(group_id))
            print('save this enroll to db2: ', new_enrolls)
            db_save_var(DB_NAME, CHAT_ID, 'enroll', str(new_enrolls))

            await MainStates.wait_for_client_answer.set()
        else:
            print('LOG: this enroll already in list')
            await bot.delete_message(CHAT_ID, accept_enroll.message_id)
            keyboard = InlineKeyboardMarkup()
            back_btn = InlineKeyboardButton('⬅️ Назад', callback_data='turn_back')
            keyboard.row(back_btn)
            await bot.send_message(CHAT_ID, 'Ви вже подавали заявку на цю групу, зачекайте обробки заявки!',
                                   reply_markup=keyboard)
            return

    elif ';clicked' in call.data:
        print('groups was clicked')
        data = call.data
        group_id = int(data[:data.find(';')])
        user_info = db_get_user_info(DB_NAME, call.from_user.id)
        user_type = user_info[0][2]
        if user_type == 'admin':
            await call.message.edit_text('Нагадування до ціеї групи', reply_markup=NotesKB(group_id))
            await AdminStates.add_note.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif ';students' in call.data:

        await call.message.edit_text('Список студентів до групи :', reply_markup=StudentsKB(group_id))

        await MainStates.students_list.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif call.data == 'turn_back':
        cur_category = db_get_save_var(DB_NAME, CHAT_ID, 'viewing_category')
        await CoursesKB(call, cur_category, state, temp_course_text)

        await MainStates.wait_for_course.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)
    else:
        return


@dp.callback_query_handler(state=MainStates.students_list)
async def student_clicked(call: types.CallbackQuery, state: FSMContext):
    print('student_clicked  data :', call.data)
    user_info = db_get_user_info(DB_NAME, call.from_user.id)
    user_type = user_info[0][2]
    if ';stud_back' in call.data:
        group_id = call.data[0:call.data.find(';')]
        group_info, course_info, to_course_id = db_get_group_info(DB_NAME, group_id)
        cur_groups = db_read_groups(DB_NAME, to_course_id)
        if user_type == 'admin':
            await MainStates.wait_for_group.set()
            keyboard = await GroupsKB(cur_groups, call.from_user.id, to_course_id, state)

            await call.message.edit_text(text=course_info, reply_markup=keyboard)
        elif user_type == 'trainer':
            await call.message.edit_text('Ваші курси:', reply_markup=MyCoursesKB(DB_NAME, call.from_user.id))

            await MainStates.show_my_courses.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)
    elif call.data.endswith('<delete'):
        group_id = call.data[0:call.data.find(';')]
        telegram_id = call.data[call.data.find(':') + 1:call.data.find('<')]
        print('tele :', telegram_id)
        db_delete_student_from_group(DB_NAME, telegram_id, group_id)
        temp_text = call.message.text
        await call.message.edit_text(temp_text, reply_markup=StudentsKB(group_id))
    else:
        telegram_id = call.data[call.data.find(':') + 1:]
        print('tele :', telegram_id)
        user_info = db_get_user_info(DB_NAME, telegram_id)
        print('info :', user_info)
        if user_type == 'admin':
            user_text = f"Ім'я: {user_info[0][0]}\nНікнейм : {user_info[0][1]}\n Телефон : {user_info[0][5]}"
        else:
            user_text = f"Ім'я: {user_info[0][0]}\nНікнейм : {user_info[0][1]}"

        await bot.answer_callback_query(call.id, user_text, True, cache_time=10)


@dp.callback_query_handler(state=MainStates.wait_for_client_answer)
async def client_answer_enroll_call(call: types.CallbackQuery, state: FSMContext):
    print('client_answer_enroll data = ', 'm: ', call.data)
    Admin_Chat = db_get_admin_group_id(DB_NAME)
    User = call.from_user
    CHAT_ID = call.message.chat.id
    if call.data == 'enroll_cancel':
        user_info = db_get_user_info(DB_NAME, CHAT_ID)
        db_delete_enroll(DB_NAME, CHAT_ID, int(user_info[1]))

        enroll_question_msg = db_get_save_var(DB_NAME, CHAT_ID, 'temp_var')

        await bot.delete_message(CHAT_ID, int(enroll_question_msg))
        await bot.send_message(CHAT_ID, '<b> 📜 Головне Меню 📜 </b> ', parse_mode='HTML',
                               reply_markup=MenuKB(call.from_user.id))
        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif call.data == 'enroll_accept':
        user_info, enroll_id, groups_id, all_enrolls = db_get_user_info(DB_NAME, CHAT_ID)

        to_admin_text = f"<strong>Получена новая заявка</strong>\n\nИмя: <i>{user_info[0]}</i>;" \
                        f"\nНикнейм: @{user_info[1]};\nТелефон: {user_info[5]}\n\nТекущие курсы: \n"
        for group in user_info[3]:
            if group[0] or group[1] is not None:
                to_admin_text += '✅' + 'Курс :' + str(group[0]) + ';\n\t ▶️ Група' + str(group[1]) + '\n'
        to_admin_text += '\nЗаявка подана на:\n'
        enroll = user_info[4][-1]
        to_admin_text += '❓' + 'Курс :' + str(enroll[0]) + '; \n\t▶️ Група' + str(enroll[1]) + '\n'
        keyboard = InlineKeyboardMarkup()

        accept_btn = InlineKeyboardButton('Підтвердити✅', callback_data=str(enroll_id) + 'T_ID:' + str(
            call.message.chat.id) + ';accept')

        cancel_btn = InlineKeyboardButton('Відхилити❌', callback_data=str(enroll_id) + 'T_ID:' + str(
            call.message.chat.id) + ';cancel_enroll')
        keyboard.row(accept_btn, cancel_btn)
        print('to admin text = ', to_admin_text)
        try:
            user_photo = await User.get_profile_photos(limit=1)
            photo_id = user_photo['photos'][0][0]['file_id']
            await bot.send_photo(Admin_Chat, photo_id, to_admin_text, 'HTML', reply_markup=keyboard)
        except:
            await bot.send_message(Admin_Chat, to_admin_text, 'HTML', reply_markup=keyboard)
        enroll_question_msg = db_get_save_var(DB_NAME, CHAT_ID, 'temp_var')

        await bot.delete_message(CHAT_ID, int(enroll_question_msg))
        await bot.send_message(CHAT_ID, '<b> 📜 Головне Меню 📜 </b> ', parse_mode='HTML',
                               reply_markup=MenuKB(CHAT_ID))

        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.message_handler(content_types=['text', 'contact'], state=MainStates.wait_for_client_answer)
async def client_answer_enroll_message(message: types.Message, state: FSMContext):
    print('client_answer_enroll message = ', 'm: ', message.text)
    Admin_Chat = db_get_admin_group_id(DB_NAME)
    User = message.from_user
    CHAT_ID = message.chat.id
    if message.text == 'Ні':
        user_info = db_get_user_info(DB_NAME, CHAT_ID)
        db_delete_enroll(DB_NAME, CHAT_ID, int(user_info[1]))

        enroll_question_msg = db_get_save_var(DB_NAME, CHAT_ID, 'temp_var')

        await bot.delete_message(CHAT_ID, int(enroll_question_msg))
        await bot.send_message(CHAT_ID, '<b> Ви відмінили відправку заявки </b> ', parse_mode='HTML',
                               reply_markup=MenuKB(message.from_user.id))
        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif message.content_type == 'contact' or message.text == 'Так':
        phone = db_get_save_var(DB_NAME, CHAT_ID, 'contacts')
        if phone == 'empty_number':
            db_save_var(DB_NAME, CHAT_ID, 'contacts', message.contact.phone_number)

        user_info, enroll_id, groups_id, all_enrolls = db_get_user_info(DB_NAME, CHAT_ID)

        to_admin_text = f"<strong>Получена новая заявка</strong>\n\nІм'я: <i>{user_info[0]}</i>;" \
                        f"\nНікнейм: @{user_info[1]};\nТелефон: {user_info[5]}\n\nЗаписан(а) на курсы: \n"
        for group in user_info[3]:
            if group[0] or group[1] is not None:
                to_admin_text += '✅' + 'Курс :' + str(group[0]) + ';\n\t ▶️ Група' + str(group[1]) + '\n'
        to_admin_text += '\nЗаявка подана на:\n'
        enroll = user_info[4][-1]
        to_admin_text += '❓' + 'Курс :' + str(enroll[0]) + '; \n\t▶️ Група' + str(enroll[1]) + '\n'
        keyboard = InlineKeyboardMarkup()

        accept_btn = InlineKeyboardButton('Підтвердити✅', callback_data=str(enroll_id) + 'T_ID:' + str(
            message.chat.id) + ';accept')

        cancel_btn = InlineKeyboardButton('Відхилити❌', callback_data=str(enroll_id) + 'T_ID:' + str(
            message.chat.id) + ';cancel_enroll')
        keyboard.row(accept_btn, cancel_btn)
        print('to admin text = ', to_admin_text)
        try:
            user_photo = await User.get_profile_photos(limit=1)
            photo_id = user_photo['photos'][0][0]['file_id']
            await bot.send_photo(Admin_Chat, photo_id, to_admin_text, 'HTML', reply_markup=keyboard)
        except:
            await bot.send_message(Admin_Chat, to_admin_text, 'HTML', reply_markup=keyboard)
        enroll_question_msg = db_get_save_var(DB_NAME, CHAT_ID, 'temp_var')

        await bot.delete_message(CHAT_ID, int(enroll_question_msg))
        await bot.send_message(CHAT_ID, '<b> Вашу заявку було відіслано до адміністраторів,'
                                        ' вам передзвонять щодо записі до курсу </b> ', parse_mode='HTML',
                               reply_markup=MenuKB(CHAT_ID))

        await MainStates.wait_menu_click.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)


    else:
        print('client_cancel_enroll miss data: ', message.text)


@dp.callback_query_handler(lambda c: ';accept' in c.data or ';cancel_enroll' in c.data, state='*')
async def check_client_enroll(call: types.CallbackQuery, state: FSMContext):
    print('check_client_enroll data = ', call.data)
    data = call.data
    enr_text = call.message.text
    enroll_id = data[0:data.find('T')]
    telegram_id = data[data.find(':') + 1:data.find(';')]
    group_info, course_name, to_course_id = db_get_group_info(DB_NAME, enroll_id)
    user_info = db_get_user_info(DB_NAME, telegram_id)
    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton('OK', callback_data='enroll_ok')
    keyboard.row(back_btn)
    if ';accept' in call.data:
        db_accept_enroll(DB_NAME, telegram_id, int(enroll_id))
        client_enroll_answer = f'Ваш запит на зачислення до курсу: \n▶️ {course_name}\nДо групи\n▶️ {group_info} ' \
                               f'\n\n <b>✅ПРИЙНЯТО✅</b>'
        if call.from_user.last_name is None:
            second_name = ''
        else:
            second_name = call.from_user.last_name
        admin_log_text = f" ✅\n{call.from_user.first_name} {second_name} <b>ПІДТВЕРДИЛА</b> заявку від\n" \
                         f"🎓 {user_info[0][0]} ({user_info[0][5]})\nДо групи :\n▶️ <b>{group_info}</b>\n" \
                         f"У курсі :\n🔵 <b>{course_name}</b>"
        await call.message.delete()
        await bot.send_message(telegram_id, client_enroll_answer, 'HTML', reply_markup=keyboard)
        await bot.send_message(call.message.chat.id, admin_log_text, 'HTML')
    elif ';cancel_enroll' in call.data:
        db_delete_enroll(DB_NAME, telegram_id, int(enroll_id))
        client_enroll_answer = f'Ваш запит на зачислення до курсу: \n▶️ {course_name}\nДо групи\n▶️ {group_info} ' \
                               f"\n\n<b>❎ВІДХИЛЕНО❎</b>" \
                               f"\nЯкщо, у вас є запитання обреіть зручний вам спосіб зв'язку із нами у 'Контактах'"
        if call.from_user.last_name is None:
            second_name = ''
        else:
            second_name = call.from_user.last_name
        admin_log_text = f"❌\n{call.from_user.first_name} {second_name} <b>ВІДХИЛИЛА</b> заявку від\n" \
                         f"🎓 {user_info[0][0]} ({user_info[0][5]})\nДо групи :\n▶️ <b>{group_info}</b>\n" \
                         f"У курсі :\n🔵 <b>{course_name}</b>"
        await call.message.delete()
        await bot.send_message(telegram_id, client_enroll_answer, 'HTML', reply_markup=keyboard)
        await bot.send_message(call.message.chat.id, admin_log_text, 'HTML')

    else:
        print('answer_enroll catch callback = ', call.data)


@dp.callback_query_handler(lambda c: c.data in ['0', '1', 'again', 'done'], state='*')
async def admin_add_flag(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID
    print('admin_add_flag data = ', call.data)

    CHAT_ID = call.from_user.id
    if call.data in ['0', '1']:
        await state.update_data(group_flag=call.data)
        days_keyboard = DaysKB()
        await bot.edit_message_text(chat_id=CHAT_ID, text='Отметьте день', reply_markup=days_keyboard,
                                    message_id=msgID)
        await AdminStates.add_group_days.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif call.data == 'again':
        days_keyboard = DaysKB()
        await bot.edit_message_text(chat_id=CHAT_ID, text='Отметьте день', reply_markup=days_keyboard,
                                    message_id=msgID)
        await AdminStates.add_group_days.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)

    elif call.data == 'done':
        state_data = await state.get_data()
        info_to_db = state_data['group_datetime']
        group_type = state_data['group_flag']
        to_course = state_data['group_to']
        group_id = state_data['group_id']
        await bot.edit_message_text(chat_id=CHAT_ID, text=f"Додати групу:\n{info_to_db}",
                                    message_id=msgID)
        final_info = ' '
        for info in info_to_db:
            final_info += (str(info) + '; ')
        if state_data['editing'] is True:
            db_edit_group(DB_NAME, group_id, final_info, group_type)
            text = "Інформацію відредаговано"
            await state.update_data(editing=False)
        elif state_data['editing'] is False:
            db_add_group(DB_NAME, final_info, group_type, to_course)

            text = "Додано групу"
        if group_type == '1':
            group_type = 'Оффлайн'
        else:
            group_type = 'Онлайн'

        cur_groups = db_read_groups(DB_NAME, to_course)
        keyboard = await GroupsKB(cur_groups, call.from_user.id, to_course, state)
        courses_body = get_content(HTML)

        temp_text = call.message.text
        await call.message.edit_text(temp_text, reply_markup=keyboard)

        await MainStates.wait_for_group.set()

        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(lambda c: c.data in weekdays, state=AdminStates.add_group_days)
async def admin_add_days(call: types.CallbackQuery, state: FSMContext):
    CHAT_ID = call.from_user.id

    temp_days = call.data
    await state.update_data(group_day=temp_days)
    keyboard = TimeKB()
    await bot.edit_message_text(chat_id=CHAT_ID, text='Отметьте время', reply_markup=keyboard,
                                message_id=msgID)
    await AdminStates.add_group_time.set()

    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(lambda c: c.data in daytimes, state=AdminStates.add_group_time)
async def add_time(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID
    CHAT_ID = call.from_user.id

    keyboard = InlineKeyboardMarkup()
    temp_time = call.data
    await state.update_data(group_time=temp_time)
    state_data = await state.get_data()
    group_datetime = ' (' + str(state_data['group_day']) + ')' + str(state_data['group_time'])
    datetimeList = state_data['group_datetime']
    datetimeList.append(group_datetime)
    await state.update_data(group_datetime=datetimeList)
    again_btn = InlineKeyboardButton('Додати час', callback_data='again')
    done_btn = InlineKeyboardButton('Завершити', callback_data='done')
    keyboard.row(again_btn)
    keyboard.row(done_btn)
    await bot.edit_message_text(chat_id=CHAT_ID, text='Процес додавання групи', reply_markup=keyboard,
                                message_id=msgID)
    await AdminStates.add_group_flag.set()

    user_state = await StateName(state)
    db_upd_user_state(DB_NAME, CHAT_ID, user_state)


GROUP_ID = None


@dp.callback_query_handler(state=AdminStates.add_note)
async def new_notification(call: types.CallbackQuery, state: FSMContext):
    global GROUP_ID
    print('new_notification data = ', call.data)
    if ';add_note' in call.data:
        data = call.data
        group_id = int(data[:data.find(';')])
        await state.update_data(group_id=group_id)
        GROUP_ID = group_id
        keyboard = EngDaysKB()

        await call.message.edit_text('Оберіть день нагадування', reply_markup=keyboard)

    if call.data in eng_weekdays:
        note_day = call.data
        await state.update_data(note_day=note_day)

        keyboard = TimeKB()

        await call.message.edit_text('Оберіть час нагадування', reply_markup=keyboard)
    if call.data in daytimes:
        note_time = call.data

        await state.update_data(note_time=note_time)

        state_data = await state.get_data()
        note_daytime = f"({state_data['note_day']})[{state_data['note_time']}];"
        db_add_notification(DB_NAME, state_data['group_id'], note_daytime)

        await call.message.edit_text('Нагадування до ціеї групи', reply_markup=NotesKB(GROUP_ID))

    if ';remove' in call.data:
        data = call.data
        group_id = int(data[data.find(':')+1:])
        note_id = int(data[0:data.find(';')])
        print('remove note id = ', note_id)
        db_delete_notification(DB_NAME, note_id)
        await call.message.edit_text('Нагадування до ціеї групи :', reply_markup=NotesKB(group_id))

    if ';turn_back' in call.data:
        group_id = int(call.data[0:call.data.find(';')])

        group_info, course_info, to_course_id = db_get_group_info(DB_NAME, group_id)
        print(group_id, '___', group_info, course_info, to_course_id)
        cur_groups = db_read_groups(DB_NAME, to_course_id)
        keyboard = await GroupsKB(cur_groups, call.from_user.id, to_course_id, state)

        await call.message.edit_text(course_info, reply_markup=keyboard)
        await MainStates.wait_for_group.set()
        user_state = await StateName(state)
        db_upd_user_state(DB_NAME, CHAT_ID, user_state)


@dp.callback_query_handler(lambda c: c.data == 'client_read_note')
async def note_was_readed(call: types.CallbackQuery):
    await call.message.delete()


async def job():
    print('job...')
    now_time = datetime.now()
    morning = datetime.now().replace(hour=9, minute=00)
    day = datetime.now().replace(hour=12, minute=00)
    evening = datetime.now().replace(hour=18, minute=00)
    cur_day = now_time.strftime('%A')
    notif_list = db_read_notification(DB_NAME)
    user_list = db_read_users(DB_NAME)
    for notification in notif_list:
        note_status = notification[3]
        note_id = notification[0]

        note_day = str(notification[2])
        note_day = note_day[note_day.find('(') + 1:note_day.find(')')]

        note_hour = str(notification[2])
        note_hour = int(note_hour[note_hour.find('[') + 1:note_hour.find(':')])

        note_minute = str(notification[2])
        note_minute = int(note_minute[note_minute.find(':') + 1:note_minute.find(']')])
        print(cur_day, 'VS', note_day)
        if cur_day == note_day:
            print('match day')
            note_time = datetime.today().replace(hour=note_hour, minute=note_minute)

            res = (note_time - now_time).__abs__().total_seconds()
            dif_hours = int(res // 3600)
            dif_minutes = int((res % 3600) // 60)
            dif_seconds = int(res % 60)

            difference = datetime.now().replace(hour=dif_hours, minute=dif_minutes, second=dif_seconds)
            timer_10 = datetime.now().replace(hour=0, minute=10, second=0)
            print(notification)
            print(difference)
            if difference <= timer_10 and note_status == 'wait':
                for user in user_list:
                    print(user)
                    user_groups = str_to_list(user[5])
                    if user[4] == 'client' and notification[1] in user_groups:
                        group_info, course_name, to_course_id = db_get_group_info(DB_NAME, notification[1])
                        keyboard = InlineKeyboardMarkup()
                        ok_btn = InlineKeyboardButton('Прочитано', callback_data='client_read_note')
                        keyboard.row(ok_btn)
                        greet = "Привіт"
                        if morning < now_time < day:
                            greet = 'Доброго ранку, '
                        elif day < now_time < evening:
                            greet = 'Добрий день, '
                        elif evening < note_time:
                            greet = 'Добрий вечір, '
                        note_text = f"{greet}{user[2]}, освітній ценр ЯІМОЯШКОЛА, нагадує вам, " \
                                    f"що ближчим чаосом ми чекаємо вас на заняття у групі <b>{group_info}</b> " \
                                    f"до курсу <b>{course_name}</b>"
                        print('note sended to user :\n',note_text)
                        await bot.send_message(chat_id=user[1], text=note_text,parse_mode='HTML', reply_markup=keyboard)
                    db_change_notification_status(DB_NAME, note_id)
            elif difference > timer_10 and note_status == 'sended':
                db_change_notification_status(DB_NAME, note_id)
    print('end job!!!!!')


@dp.message_handler(lambda m: '/start' not in m.text, state=None)
async def check_state_for_user_message(message: types.Message, state: FSMContext):
    global CHAT_ID
    needed_state = db_get_user_state(DB_NAME, message.chat.id)
    await state.set_state(needed_state)
    CHAT_ID = message.chat.id
    now_state = await state.get_state()
    print('catched message = ', message.text)
    print('need', needed_state)
    print('have', now_state)




@dp.callback_query_handler(state=None)
async def check_state_for_user_callback(call: types.CallbackQuery, state: FSMContext):
    global CHAT_ID
    needed_state = db_get_user_state(DB_NAME, call.message.chat.id)
    now_state = await state.get_state()
    print('have', now_state)
    CHAT_ID = call.message.chat.id
    now_state = await state.get_state()
    print('needed_state = ', needed_state)
    await state.set_state(needed_state)
    print('catched callback = ', call.data)


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.call_later(DELAY, repeat, job, loop)
    executor.start_polling(dp)
