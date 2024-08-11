from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from crud_functions import initiate_db, get_all_products

API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Рассчитать'))
keyboard.add(KeyboardButton('Информация'))
keyboard.add(KeyboardButton('Купить'))

inline_keyboard = InlineKeyboardMarkup()
inline_keyboard.add(InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories'))
inline_keyboard.add(InlineKeyboardButton('Формулы расчёта', callback_data='formulas'))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Я бот, помогающий твоему здоровью. Чем могу помочь?", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.reply("Выберите опцию:", reply_markup=inline_keyboard)

@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    await call.message.reply("Формула Миффлина-Сан Жеора для расчёта нормы калорий:\n\n"
                             "Для мужчин: (10 × вес в кг) + (6.25 × рост в см) - (5 × возраст в годах) + 5\n"
                             "Для женщин: (10 × вес в кг) + (6.25 × рост в см) - (5 × возраст в годах) - 161")

@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery):
    await call.message.reply("Введите свой возраст:")
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = int(message.text)
    await message.reply("Введите свой рост:")
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['growth'] = int(message.text)
    await message.reply("Введите свой вес:")
    await UserState.weight.set()

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['weight'] = int(message.text)
        age = data['age']
        growth = data['growth']
        weight = data['weight']

    calories = 10 * weight + 6.25 * growth - 5 * age + 5

    await message.reply(f"Ваша норма калорий: {calories} ккал в день.")
    await state.finish()


@dp.message_handler(lambda message: message.text == 'Информация')
async def send_info(message: types.Message):
    await message.reply("Я бот, помогающий рассчитать вашу дневную норму калорий. Используйте кнопку 'Рассчитать' для начала.")

@dp.message_handler(lambda message: message.text == 'Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()
    for product in products:
        await message.reply(f"Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}")
        if product[4]:
            await message.reply_photo(photo=open(product[4], 'rb'))

@dp.callback_query_handler(lambda call: call.data.startswith('product_'))
async def send_confirm_message(call: types.CallbackQuery):
    product_name = call.data.split('_')[1]
    await call.message.reply(f"Вы успешно приобрели продукт: Витамин {product_name}!")

if __name__ == '__main__':
    initiate_db()
    executor.start_polling(dp, skip_updates=True)