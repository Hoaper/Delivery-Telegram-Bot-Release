import os, json
from aiogram import types, Dispatcher, Bot, executor
from dotenv import load_dotenv
from config import *
import sqlite3


# PATHS
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
path_langs = os.path.join(os.path.dirname(__file__), "db", "locales.db")
path_orders = os.path.join(os.path.dirname(__file__), "db", "orders.db")
path_steps = os.path.join(os.path.dirname(__file__), "db", "steps.db")
path_pre_order = os.path.join(os.path.dirname(__file__), "db", "pre_order.db")

# AVAILABLE LANGS
supported_langs = {"🇷🇺 Русский 🇷🇺": "ru", "🇺🇸 English 🇺🇸": "eng", "🇺🇿 O\'zbekcha 🇺🇿": "uzb"}

# DB INIT
db_lang = sqlite3.connect(path_langs)
lang_cur = db_lang.cursor()
db_orders = sqlite3.connect(path_orders)
orders_cur = db_orders.cursor()
db_steps = sqlite3.connect(path_steps)
steps_cur = db_steps.cursor()
db_pre_order = sqlite3.connect(path_pre_order)
pre_order_cursor = db_pre_order.cursor()

# TABLE CREATING
lang_cur.execute("""CREATE TABLE IF NOT EXISTS lang(
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    language VARCHAR);""")
db_lang.commit()

orders_cur.execute("""CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    menu TEXT,
    status VARCHAR,
    number TEXT);""")
db_orders.commit()

steps_cur.execute("""CREATE TABLE IF NOT EXISTS steps(
    id INTEGER PRIMARY KEY,
    chat_id INTEGER UNIQUE,
    state VARCHAR);""")
db_steps.commit()

pre_order_cursor.execute("""CREATE TABLE IF NOT EXISTS pre_order(
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    name VARCHAR,
    type VARCHAR,
    count INTEGER,
    cost_per_one INTEGER,
    category VARCHAR);""")
db_orders.commit()

# KEYBOARDS
lang_kb = types.reply_keyboard.ReplyKeyboardMarkup([], resize_keyboard=True)
for lang in supported_langs.keys():
    lang_kb.row(types.KeyboardButton(lang))

# .ENV
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# BOT INIT
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)

# FUNCTIONS
# FUNCTIONS -> GETs
def getLocale(lang_id: str) -> dict:
    locales_path = os.path.join(os.path.dirname(__file__), "locales.json")
    _return = {}
    with open(locales_path, "r") as files:

        _return = json.load(files)[lang_id]

    return _return

def getLangId(msg: types.Message) -> str:
    lang_cur.execute("SELECT language FROM lang WHERE chat_id=?", (msg.chat.id, ))
    return lang_cur.fetchone()[0] or None

def getFood() -> dict:
    
    with open("food.json", "r") as f:
        return json.load(f)

def getMenuKB(lang_id: str) -> types.reply_keyboard.ReplyKeyboardMarkup:
    menu_locale = getLocale(lang_id)['main_menu']

    return types.reply_keyboard.ReplyKeyboardMarkup([
        [types.KeyboardButton(f"{menu_locale['menu']}")],
        [types.KeyboardButton(f"{menu_locale['orders']}")],
        [
            types.KeyboardButton(f"{menu_locale['review']}"),
            types.KeyboardButton(f"{menu_locale['settings']}")
        ]

    ], resize_keyboard=True)

def getSettingsKB(lang_id: str) -> types.reply_keyboard.ReplyKeyboardMarkup:
    settings_locale = getLocale(lang_id)
    return types.reply_keyboard.ReplyKeyboardMarkup([
        [types.KeyboardButton("/lang")],
        [types.KeyboardButton(settings_locale['back'])]
    ], resize_keyboard=True)

def getLocationKB(lang_id: str) -> types.reply_keyboard.ReplyKeyboardMarkup:

    locale = getLocale(lang_id)

    return types.reply_keyboard.ReplyKeyboardMarkup([
        [types.KeyboardButton(text=locale['location']['geo'], request_contact=True)],
        [
            types.KeyboardButton(text=locale['location']['adress']),
            types.KeyboardButton(text=locale['back'])
        ]
    ], resize_keyboard=True)

def getFoodMenuKB(lang_id: str, is_cart: bool) -> types.reply_keyboard.ReplyKeyboardMarkup:
    
    try:
        locale = getLocale(lang_id)
        if is_cart:
            keyboard = types.reply_keyboard.ReplyKeyboardMarkup([
                [types.KeyboardButton(locale['cart']['title'])] 
            ], resize_keyboard = True, row_width=2)
        else:
            keyboard = types.reply_keyboard.ReplyKeyboardMarkup([], resize_keyboard=True, row_width=2)

        food_list = getFood()
        for _, category in food_list.items():

            keyboard.insert(types.KeyboardButton(category[lang_id]['title']))
        
        keyboard.row(types.KeyboardButton(locale['back']))

        return keyboard


    except:
        return types.reply_keyboard.ReplyKeyboardMarkup(
            [
                types.KeyboardButton("FAIL CONTACT @zh0per"), 
                types.KeyboardButton(locale['back'])
            ], resize_keyboard=True)

def getSpecificFoodMenuKB(lang_id, menu: dict, is_cart: bool) -> types.reply_keyboard.ReplyKeyboardMarkup:
    
    try:
        locale = getLocale(lang_id)

        if is_cart:
            keyboard = types.reply_keyboard.ReplyKeyboardMarkup([
                [types.KeyboardButton(locale['cart']['title'])] 
            ], resize_keyboard = True, row_width=2)
        else:
            keyboard = types.reply_keyboard.ReplyKeyboardMarkup([], resize_keyboard=True, row_width=2)

        for item in menu['list'].keys():

            keyboard.insert(types.KeyboardButton(item))

        keyboard.row(types.KeyboardButton(locale['back']))

        return keyboard


    except:
        locale = getLocale(lang_id)
        return types.reply_keyboard.ReplyKeyboardMarkup(
            [
                types.KeyboardButton("FAILED, CONTACT @zh0per"), 
                types.KeyboardButton(locale['back'])
            ], resize_keyboard=True)
    
def getCostsKB(lang_id: str, category: dict, item: str):
    localed_back = getLocale(lang_id)['back']
    kb = types.reply_keyboard.ReplyKeyboardMarkup([], resize_keyboard=True, row_width=2)
    try:
        for mass, cost in category['list'][item].items():
            kb.insert(types.KeyboardButton(mass))
        kb.row(
            types.KeyboardButton(localed_back)
        )
        return kb

    except:
        return types.reply_keyboard.ReplyKeyboardMarkup([
            types.KeyboardButton("Something went wrong! @zh0per can help you")
        ])

def getInlineCartKB(lang_id: str, _type, name, category, cost, value=1):
    
    localed_add = getLocale(lang_id)['add_to_cart']

    kb = types.InlineKeyboardMarkup()
    kb.row(
            types.InlineKeyboardButton(text="-", callback_data=f"minus_{category}_{name}_{_type}_{value}_{cost}"),
            types.InlineKeyboardButton(text=value, callback_data="nothing"),
            types.InlineKeyboardButton(text="+", callback_data=f"plus_{category}_{name}_{_type}_{value}_{cost}")
        )
    kb.row(types.InlineKeyboardButton(localed_add, callback_data=f"add_{category}_{name}_{_type}_{value}_{cost}"))
    return kb

# FUNCTIONS -> SET
def setState(msg, state):

    steps_cur.execute("""INSERT INTO steps(chat_id, state)
                        VALUES (?, ?)
                        ON CONFLICT(chat_id) DO 
                        UPDATE SET state=? WHERE chat_id=?""", 
                        (msg.chat.id, state, state, msg.chat.id)
                    )
    db_steps.commit()

# FUNCTIONS -> CHECKs
def checkSettingsLocale(msg: types.Message) -> bool:
    try:
        lang_id = getLangId(msg)
        return msg.text == getLocale(lang_id)['main_menu']['settings']
    except:
        return False

def checkReviewLocale(msg: types.Message) -> bool:
    try:
        lang_id = getLangId(msg)
        return msg.text == getLocale(lang_id)['main_menu']['review']
    except:
        return False

def checkReviewBackLocale(msg: types.Message) -> bool:

    try:
        lang_id = getLangId(msg)

        if checkStateLocale(msg, "review") and msg.text == getLocale(lang_id)['back']:
            steps_cur.execute("DELETE FROM steps WHERE chat_id=?", (msg.chat.id, ))
            db_steps.commit()
            return True
    except:
        return False

def checkReviewSendLocale(msg: types.Message) -> bool:
    try:
        lang_id = getLangId(msg)

        if checkStateLocale(msg, "review") and msg.text != getLocale(lang_id)['back']:
            steps_cur.execute("DELETE FROM steps WHERE chat_id=?", (msg.chat.id, ))
            db_steps.commit()

            return True

    except:
        return False

def checkSettingsBack(msg: types.Message) -> bool:

    try:
        lang_id = getLangId(msg)

        if checkStateLocale(msg, "settings") and msg.text == getLocale(lang_id)['back']:
            steps_cur.execute("DELETE FROM steps WHERE chat_id=?", (msg.chat.id, ))
            db_steps.commit()

            return True

    except:
        return False

def checkMenuBack(msg: types.Message) -> bool:

    try:
        lang_id = getLangId(msg)
        if checkStateLocale(msg, "ordering") and msg.text == getLocale(lang_id)['back']:
            steps_cur.execute("DELETE FROM steps WHERE chat_id=?", (msg.chat.id, ))
            db_steps.commit()

            return True

    except Exception as e:
        return False

def checkStateLocale(msg: types.Message, status) -> bool:
    try:
        steps_cur.execute("SELECT * FROM steps WHERE chat_id=?;", (msg.chat.id, ))
        _id, _, state = steps_cur.fetchone()
        if state == status:

            return True


        else:
            raise Exception()


    except Exception as e:

        return False

def checkCartLocale(msg: types.Message) -> bool:

    try:
        lang_id = getLangId(msg)
        locale = getLocale(lang_id)

        return msg.text == locale['cart']['title']
    
    except:
        return False
# NEEDED IN REMAKE (do not touch idk what is it)
def checkAdressLocale(msg: types.Message) -> bool:
    try:
        localed_menu = getLocale(getLangId(msg))['main_menu']['menu']
        return localed_menu == msg.text

    except:
        return False

def checkMyOfficesLocale(msg: types.Message) -> bool:

    try:
        localed_geo = getLocale(getLangId(msg))['location']['adress']
        return localed_geo == msg.text
    except:
        return False

def checkMenuLocale(msg: types.Message) -> bool:
    
    try:
        locale = getLocale(getLangId(msg))
        return locale['main_menu']['menu'] == msg.text

    except:

        return False

def checkTitleInMenu(msg: types.Message) -> bool:

    try:

        lang_id = getLangId(msg)
        food = getFood()

        for _, category in food.items():
            if category[lang_id]['title'] == msg.text:
                return True

        return False
    except Exception as e:
        return False

def checkSpecifiedStateBackLocale(msg: types.Message) -> bool:
    try:
        localed_back = getLocale(getLangId(msg))['back']
        return checkStateLocale(msg, "specified_ordering") and msg.text == localed_back
    except:
        return False

def checkSpecifiedTitles(msg: types.Message) -> bool:
    try:
        steps_cur.execute("SELECT state FROM steps WHERE chat_id=?", (msg.chat.id, ))
        fetched = steps_cur.fetchone()[0]
    except:
        return False
    if fetched:

        return fetched == "specified_ordering" and msg.text[0] != "/"

    else:
        return False

def checkMassChoosed(msg: types.Message) -> bool:

    steps_cur.execute("SELECT state FROM steps WHERE chat_id=?", (msg.chat.id, ))
    pre_order_cursor.execute("SELECT name, category FROM pre_order WHERE chat_id=? AND count IS NULL", (msg.chat.id, ))
    try:
        name, category = pre_order_cursor.fetchone()
        fetched = steps_cur.fetchone()[0]
    except:
        return False

    if fetched and name:
        _return = False
        for kilo, cost in getFood()[category]['list'][name].items():
            if kilo == msg.text:
                _return = True
                break

        return fetched == "cost_choosing" and _return

    else:
        return False

def checkSubMenuBackLocale(msg: types.Message) -> bool:
    try:
        localed_back = getLocale(getLangId(msg))['back']
        return checkStateLocale(msg, "cost_choosing") and msg.text == localed_back

    except:
        return False

def checkAddCallBack(callback: types.CallbackQuery) -> bool:
    return callback.data.split("_")[0] == "plus"

def checkMinusCallback(callback: types.CallbackQuery) -> bool:
    return callback.data.split("_")[0] == "minus"

def checkAddToCartCallBack(callback: types.CallbackQuery) -> bool:
    return callback.data.split("_")[0] == "add"

def checkDeleteFromCartCallBack(callback: types.CallbackQuery) -> bool:
    return callback.data.split("_")[0] == "delete"

def checkOrdersLocale(msg: types.Message) -> bool:
    try:
        locale = getLocale(getLangId(msg))
        return msg.text == locale['main_menu']['orders']
    except:
        return False

def checkPassword(msg: types.Message) -> bool:
    try:
        _, pswd = msg.text.split(" ")
        return pswd == os.getenv("DUMP_PASSWORD")

    except:
        return False

# HANDLERS
# HANDLERS -> start
@dp.message_handler(commands=['start', 'language', 'lang'])
async def start(msg: types.Message):

    await msg.answer(text="Выберите язык!", reply_markup=lang_kb)

# HANDLERS -> main menu
@dp.message_handler(commands=['menu'])
async def show_menu(msg: types.Message):
    lang_id = getLangId(msg)
    await msg.answer(text=getLocale(lang_id)['welcome'], reply_markup=getMenuKB(lang_id))

# HANDLERS -> settings
@dp.message_handler(checkSettingsLocale)
async def show_settings(msg: types.Message):
    lang_id = getLangId(msg)
    text = getLocale(lang_id)['settings_menu']['menu']

    setState(msg, "settings")

    await msg.answer(text=text, reply_markup=getSettingsKB(lang_id))

# HANDLERS -> back from settings
@dp.message_handler(checkSettingsBack)
async def settings_back(msg: types.Message):

    await show_menu(msg)

# HANDLERS -> back from food_menu
@dp.message_handler(checkMenuBack)
async def food_menu_back(msg: types.Message):
    await show_menu(msg)

# HANDLERS -> My orders
@dp.message_handler(checkOrdersLocale)
async def my_orders(msg: types.Message):
    locale = getLocale(getLangId(msg))
    orders_cur.execute("SELECT id, menu, status, number FROM orders WHERE chat_id=? ORDER BY id DESC LIMIT 5", (msg.chat.id, ))
    all_orders = orders_cur.fetchall()
    if not all_orders:
        await msg.answer(locale['cart']['empty'])
        await show_menu(msg)
        return
    
    _print = locale['my_orders']
    for order in all_orders:
        _id, menu, status, address = order
        status = locale['statuses'][status]
        _print += locale['orders_template'].format(_id, menu, status, address)
        _print += "================\n"
    
    await msg.answer(_print)
    await show_menu(msg)

# HANDLERS -> review
@dp.message_handler(checkReviewLocale)
async def ask_review(msg: types.Message):
    lang_id = getLangId(msg)
    text = getLocale(lang_id)

    # REVIEW KB
    review_kb = types.reply_keyboard.ReplyKeyboardMarkup([
        [types.KeyboardButton(text['back'])]
    ], resize_keyboard=True)

    setState(msg, "review")

    await msg.answer(text['review']['handled'], reply_markup=review_kb)

# HANDLERS -> back from reveiw
@dp.message_handler(checkReviewBackLocale)
async def review_back(msg: types.Message):
    
    await show_menu(msg)

# HANDLERS -> back from specified menu
@dp.message_handler(checkSpecifiedStateBackLocale)
async def specified_back(msg: types.Message):

    await food_menu(msg)

# HANDLERS -> back from sub menu
@dp.message_handler(checkSubMenuBackLocale)
async def sub_menu_back(msg: types.Message):

    try:
        name = pre_order_cursor.execute("SELECT name FROM pre_order WHERE chat_id=? AND count IS NULL", (msg.chat.id, )).fetchone()[0]
        pre_order_cursor.execute("DELETE FROM pre_order WHERE name=? AND chat_id=? AND count IS NULL", (name, msg.chat.id))
        db_pre_order.commit()
    except:
        pass
    _category = None
    food = getFood()
    for category, items in food.items():
        _break = False
        for _name, price in items['list'].items():
            if _name == name:
                _category = category
                _break = True
                break

        if _break:
            break
    await specified_menu(msg, category) 

# HANDLERS -> send review
@dp.message_handler(checkReviewSendLocale)
async def review_send(msg: types.Message):

    locale = getLocale(getLangId(msg))
    await bot.send_message(REVIEW_CHANNEL_ID, f"⭐ Review from {msg.from_user.full_name}:\n{msg.text}")
    await msg.answer(locale['review']['sent'])
    await show_menu(msg)

# HANDLERS -> change lang
@dp.message_handler(lambda msg: msg.text in supported_langs)
async def change_lang(msg: types.Message):

    lang_cur.execute("SELECT * FROM lang WHERE chat_id=?", (msg.chat.id, ))

    lang_id = supported_langs[msg.text]

    try:
        # existed user screnario
        _id, chat_id, lang = lang_cur.fetchone()

        if msg.text != lang:

            lang_cur.execute("UPDATE lang SET language=? WHERE id=?", (supported_langs[msg.text], _id))
            db_lang.commit()
            await msg.answer(getLocale(lang_id)['lang_change'])

    except:
        # new user scenario
        lang_cur.execute("INSERT INTO lang(chat_id, language) VALUES (?, ?)", (msg.chat.id, lang_id))
        db_lang.commit()

    finally:
        # menu
        await msg.answer(text=getLocale(lang_id)['welcome'], reply_markup=getMenuKB(lang_id))

# HANDLERS -> cart
@dp.message_handler(checkCartLocale)
async def cart(msg: types.Message):

    try:
        lang_id = getLangId(msg)
        locale = getLocale(lang_id)['cart']

        pre_order_cursor.execute(
            "SELECT id, name, type, count, cost_per_one FROM pre_order WHERE chat_id=?",
            (msg.chat.id,)
        )
        pre_orders = pre_order_cursor.fetchall()

        if not pre_orders:
            raise Exception("Empty cart")

        await msg.answer(locale['header'])
        _print = ""
        _cost = 0
        count = 1
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.row(types.InlineKeyboardButton(text=locale['order_now'], callback_data="order_now"))
        for pre_order in pre_orders:
            _id, name, _type, _count, cost_per_one = pre_order
            _print += locale['template'].format(str(count), name, _type, _count, cost_per_one)
            count += 1
            kb.row(
                types.InlineKeyboardButton(
                    text=f"❌ {name} {_type} {_count}", 
                    callback_data=f"delete_{_id}")
            )
            _cost += int(_count) * int(cost_per_one)
        


        await msg.answer(
            _print + locale['summ'].format(_cost), reply_markup=kb
        )
    
    except Exception as e:
        pre_order_cursor.execute("DELETE FROM pre_order WHERE chat_id=?", (msg.chat.id, ))
        db_pre_order.commit()
        try:
            lang_id = getLangId(msg)
            locale = getLocale(lang_id)['cart']
            await msg.answer(locale['empty'])

        except:
            pass
        
        await show_menu(msg)

# HANDLERS -> food menu
@dp.message_handler(checkMenuLocale)
async def food_menu(msg: types.Message):

    pre_order_cursor.execute("SELECT * FROM pre_order WHERE chat_id=? and type IS NOT NULL", (msg.chat.id,))
    existed_order = pre_order_cursor.fetchone()

    lang_id = getLangId(msg)
    locale = getLocale(lang_id)

    kb = getFoodMenuKB(lang_id, bool(existed_order))

    setState(msg, "ordering")

    await msg.answer(locale['select_food_menu'], reply_markup=kb)

# HANDLERS -> specified menu
@dp.message_handler(checkTitleInMenu)
async def specified_menu(msg: types.Message, _category=None):
    lang_id = getLangId(msg)
    locale = getLocale(lang_id)
    food = getFood()
    for category, item in food.items():
        if item[lang_id]['title'] == msg.text or category == _category:
            food = food[category]
            break

    pre_order_cursor.execute("SELECT * FROM pre_order WHERE chat_id=?", (msg.chat.id,))
    existed_order = pre_order_cursor.fetchone()

    setState(msg, "specified_ordering")
    path = types.input_file.InputFile(food[lang_id]['img'])
    await msg.answer_photo(
        photo=path, 
        reply_markup=getSpecificFoodMenuKB(lang_id, food, bool(existed_order))
    )

@dp.message_handler(checkSpecifiedTitles)
async def specified_food(msg: types.Message, _key=None):
    lang_id = getLangId(msg)
    localed_choose = getLocale(lang_id)['sub_category']
    food = getFood()
    _db_category = ""
    _category = {}
    _item = ""
    for category, item in food.items():
        _break = False
        for key, _ in item['list'].items():

            if key == msg.text or _key == key:
                _category = food[category]
                _db_category = category
                _item = key
                _break = True
                break

        if _break:
            break  

    setState(msg, "cost_choosing")

    pre_order_cursor.execute(
        "INSERT INTO pre_order(chat_id, name, category) VALUES (?, ?, ?)", 
        (msg.chat.id, msg.text, _db_category)
    )
    db_pre_order.commit()
    try:
        await msg.answer(localed_choose, reply_markup=getCostsKB(lang_id, _category, _item))
    except:
        setState(msg, "specified_ordering")

@dp.message_handler(checkMassChoosed)
async def specified_cost(msg: types.Message):
    lang_id = getLangId(msg)
    locale = getLocale(lang_id)
    localed_description = getLocale(lang_id)['pre_order_desc']
    _id, name, category = pre_order_cursor.execute(
        "SELECT id, name, category FROM pre_order WHERE chat_id=? AND count IS NULL", 
        (msg.chat.id, )).fetchone()
    food = getFood()[category]
    cost = food['list'][name][msg.text]
    _print = localed_description.format(name, msg.text, cost)
    if category in ["meat", "hot-food"]:
        _print += f"\n{locale['cooking_warning']}"

    await msg.answer(
            _print, 
            reply_markup=getInlineCartKB(lang_id, msg.text, name, category, cost)
        )

# HANDLERS -> NUMBER HANDLER
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def catch_number(msg: types.Message):
    lang_id = getLangId(msg)
    locale = getLocale(lang_id)
    number = msg.contact['phone_number']

    pre_order_cursor.execute("SELECT name, type, count, cost_per_one FROM pre_order WHERE chat_id=?", (msg.chat.id, ))
    data = pre_order_cursor.fetchall()

    _print = ""
    _count = 1
    _cost = 0
    for item in data:
        name, _type, count, cost = item
        _print += locale['cart']['accept_item'].format(
            _count, name, _type, count, str(int(count) * int(cost))
        ) + "\n"
        _cost += int(cost) * int(count)
        _count += 1 

    _print += locale['cart']['summ'].format(str(_cost))

    orders_cur.execute(
        "INSERT INTO orders(chat_id, menu, status, number) VALUES (?, ?, ?, ?)",
        (msg.chat.id, _print, "processing", number)
    )
    _print = locale['cart']['accept_header'] + _print

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton(text=locale['cart']['accept_btn'], callback_data=f"accept"),
        types.InlineKeyboardButton(text=locale['cart']['discard_btn'], callback_data="discard")
    )

    await msg.answer(text=_print, reply_markup=kb)

@dp.message_handler(checkMyOfficesLocale)
async def see_offices(msg: types.Message):
    locale = getLocale(getLangId(msg))
    await msg.answer(locale['offices'])

# CALLBACK QUERIES (HARD LEVEL)
@dp.callback_query_handler(checkAddCallBack)
async def adding_count(callback: types.CallbackQuery):
    lang_id = getLangId(callback.message)
    prefix, category, name, _type, value, cost = callback.data.split("_")

    await callback.message.edit_reply_markup(getInlineCartKB(lang_id, _type, name, category, cost, int(value) + 1))

@dp.callback_query_handler(checkMinusCallback)
async def minus_count(callback: types.CallbackQuery):
    lang_id = getLangId(callback.message)
    prefix, category, name, _type, value, cost = callback.data.split("_")
    if int(value) == 1:
        return
    await callback.message.edit_reply_markup(getInlineCartKB(lang_id, _type, name, category, cost, int(value) - 1))

@dp.callback_query_handler(checkAddToCartCallBack)
async def add_to_cart(callback: types.CallbackQuery):
    lang_id = getLangId(callback.message)
    prefix, category, name, _type, value, cost = callback.data.split("_")
    pre_order_cursor.execute(
        "UPDATE pre_order SET type=?, count=?, cost_per_one=? WHERE chat_id=? AND name=?", 
        (_type, int(value), cost, callback.message.chat.id, name)
    )
    
    await food_menu(callback.message)

@dp.callback_query_handler(checkDeleteFromCartCallBack)
async def delete_from_cart(callback: types.CallbackQuery):
    _id = callback.data.split("_")[-1]
    pre_order_cursor.execute("SELECT * FROM pre_order WHERE chat_id=?", (callback.message.chat.id, )) 
    fetched = pre_order_cursor.fetchall()
    pre_order_cursor.execute("DELETE FROM pre_order WHERE id=?", (_id))
    db_pre_order.commit()
    if len(fetched) == 1:
        await food_menu(callback.message)
    else:
        msg = callback.message
        lang_id = getLangId(msg)
        locale = getLocale(lang_id)['cart']

        pre_order_cursor.execute(
            "SELECT id, name, type, count, cost_per_one FROM pre_order WHERE chat_id=?",
            (msg.chat.id,)
        )
        pre_orders = pre_order_cursor.fetchall()

        if not pre_orders:
            raise Exception("Empty cart")

        _print = ""
        count = 1
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.row(types.InlineKeyboardButton(text=locale['order_now'], callback_data="order_now"))
        for pre_order in pre_orders:
            _id, name, _type, _count, cost_per_one = pre_order
            _print += locale['template'].format(str(count), name, _type, _count, cost_per_one)
            count += 1
            kb.row(
                types.InlineKeyboardButton(
                    text=f"❌ {name} {_type} {_count}", 
                    callback_data=f"delete_{_id}")
            )
        await callback.message.edit_text(
                text=_print + locale['summ'].format(int(cost_per_one)*int(_count)),
                reply_markup=kb
            )

@dp.callback_query_handler(lambda x: x.data=="order_now")
async def ask_geo(cb: types.CallbackQuery):
    lang_id = getLangId(cb.message)
    localed_geo = getLocale(lang_id)['main_menu']['geolocation']

    kb = getLocationKB(lang_id)
    await cb.message.answer(text=localed_geo, reply_markup=kb)

@dp.callback_query_handler(lambda x: x.data=="accept")
async def make_order(callback: types.CallbackQuery):
    lang_id = getLangId(callback.message)
    locale = getLocale("uzb")
    pre_order_cursor.execute("SELECT * FROM pre_order WHERE chat_id=?", (callback.message.chat.id, ))
    orders_cur.execute(
        "SELECT id, number FROM orders WHERE chat_id=? AND status=?", 
        (callback.message.chat.id, "processing")
    )
    _ID, number = orders_cur.fetchone()
    orders_cur.execute("UPDATE orders SET status=? WHERE id=?", ("fetched", _ID))
    db_orders.commit()

    data = pre_order_cursor.fetchall()
    if not data:
        await show_menu(callback.message)
        return

    _print = f"№{_ID}\nBuyurtmachi {callback.from_user.mention}\nNomer: {number}\nSavat:\n"
    count = 1
    _cost = 0
    kb = types.InlineKeyboardMarkup(row_width=1)
    for order in data:
        _id, _, name, _type, _count, cost_per_one, _ = order
        _print += locale['cart']['template'].format(str(count), name, _type, _count, cost_per_one)
        _cost += int(cost_per_one) * _count
        count += 1

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(
        types.InlineKeyboardButton(text="Ishlovga yuborildi...", callback_data=f"delivering_{_ID}_{lang_id}")
    )
    _print += f"\nUmumiy: {_cost}"

    pre_order_cursor.execute("DELETE FROM pre_order WHERE chat_id=?", (callback.message.chat.id, ))
    db_pre_order.commit()

    await bot.send_message(chat_id=ORDERS_CHANNEL_ID, text=_print, reply_markup=kb)
    await callback.answer(locale['thanks'])
    await show_menu(callback.message)

@dp.callback_query_handler(lambda x: x.data=="discard")
async def discard_order(cb: types.CallbackQuery):

    pre_order_cursor.execute("DELETE FROM pre_order WHERE chat_id=?", (cb.message.chat.id, ))
    db_pre_order.commit()
    orders_cur.execute(
        "DELETE FROM orders WHERE chat_id=? AND status=?", 
        (cb.message.chat.id, "processing")
    )
    await show_menu(cb.message)

@dp.callback_query_handler(lambda x: x.data.split("_")[0]=="delivering")
async def deliveryng_set(callback: types.CallbackQuery):
    _id, lang_id = callback.data.split("_")[1:]
    _id = int(_id)

    orders_cur.execute("SELECT chat_id FROM orders WHERE id=?", (_id, ))
    chat_id = orders_cur.fetchone()[0]
    orders_cur.execute("UPDATE orders SET status=? WHERE id=?", ("delivering", _id))
    db_orders.commit()
    locale = getLocale(lang_id)
    if chat_id:
        try:
            await bot.send_message(chat_id, locale['delivering'].format(_id))
            await callback.answer("Buyurtma yuborildi!")

            kb = types.InlineKeyboardMarkup(row_width=1)

            kb.row(
                types.InlineKeyboardButton(text="❌Yetkazib berildi❌", callback_data=f"arrived_{_id}_{lang_id}")
            )
            await callback.message.edit_reply_markup(kb)
        except:
            await callback.answer("Чат айди недоступен - невозможно достичь пользователя")

@dp.callback_query_handler(lambda x: x.data.split("_")[0]=="arrived")
async def order_arrived(callback: types.CallbackQuery):
    _id, lang_id = callback.data.split("_")[1:]
    _id = int(_id)

    orders_cur.execute("SELECT chat_id FROM orders WHERE id=?", (_id, ))
    chat_id = orders_cur.fetchone()[0]
    orders_cur.execute("UPDATE orders SET status=? WHERE id=?", ("arrived", _id))
    db_orders.commit()

    locale = getLocale(lang_id)
    if chat_id:
        try:
            await bot.send_message(chat_id, locale['arrived'].format(_id))
            await callback.answer("Отправлено заказчику!")

            kb = types.InlineKeyboardMarkup(row_width=1)

            kb.row(
                types.InlineKeyboardButton(text="👌Yetkazib berildi👌", callback_data="nothing")
            )
            await callback.message.edit_reply_markup(kb)
        except:
            await callback.answer("Чат айди недоступен - невозможно достичь пользователя")

@dp.message_handler(checkPassword, commands=["dump"])
async def dump_orders(msg: types.Message):

    await msg.answer_document(
        types.input_file.InputFile("db/orders.db")
    )

@dp.message_handler(commands=["clear_cart"])
async def clear_cart(msg):
    pre_order_cursor.execute('DELETE FROM pre_order WHERE chat_id=?', (msg.chat.id,))

@dp.message_handler(commands=['print_chat_id'])
async def print_chat_id(msg: types.Message):
    print(msg.chat.id)

executor.start_polling(dp)


