import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "ТВОЙ_ТОКЕН_БОТА_ОТ_BOTFATHER"
bot = Bot(token=TOKEN)
dp = Dispatcher()

ADMIN_IDS = [1116150221] 
WEBAPP_URL = "https://muffin331.github.io/Muffin_Arcade/"

users_db = {}   
promos_db = {}  

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🧁 Играть в Muffin Game", web_app=types.WebAppInfo(url=WEBAPP_URL))
    builder.button(text="⭐ Пополнить Stars", callback_data="shop_stars")
    builder.button(text="🎁 Кейсы", callback_data="shop_cases")
    builder.button(text="🎟️ Ввести промокод", callback_data="input_promo")
    builder.adjust(1, 2, 1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🧁 **Muffin Arcade — твой главный игровой хаб в Telegram!**\n\n"
        "🚀 Летай на ракете-кексе в Muffin Fly и забирай крупные иксы.\n"
        "🎁 Открывай секретные кейсы с рулеткой и выбивай подарки!\n"
        "🛍️ Обменивай накопленные Stars на реальные Telegram-подарки.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "shop_stars")
async def cb_shop_stars(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧁 Открыть магазин в Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL))
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("⭐ **Покупка Telegram Stars**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "shop_cases")
async def cb_shop_cases(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Открыть кейс в Mini App", web_app=types.WebAppInfo(url=WEBAPP_URL))
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("🎁 **Кейсы с подарками и рулеткой**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "input_promo")
async def cb_input_promo(callback: types.CallbackQuery):
    await callback.message.answer("🎟️ Отправь промокод командой:\n`/promo ТВОЙ_ПРОМОКОД`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🧁 **Muffin Arcade — твой главный игровой хаб в Telegram!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer(
        "👑 **Админ-панель**\n\n"
        "• `/give [ID] [Stars]` — выдать Stars\n"
        "• `/addpromo [КОД] [Stars] [Кол-во] [Часы]` — создать промокод",
        parse_mode="Markdown"
    )

@dp.message(Command("give"))
async def cmd_give(message: types.Message):
    if not is_admin(message.from_user.id): return
    try:
        _, uid, amount = message.text.split()
        uid, amount = int(uid), int(amount)
        users_db.setdefault(uid, {"balance": 0, "used_promos": []})["balance"] += amount
        await message.answer(f"✅ Успешно выдано `{amount}` ⭐ пользователю `{uid}`", parse_mode="Markdown")
    except:
        await message.answer("⚠️ Формат: `/give 1116150221 100`", parse_mode="Markdown")

@dp.message(Command("addpromo"))
async def cmd_addpromo(message: types.Message):
    if not is_admin(message.from_user.id): return
    try:
        _, code, reward, max_uses, hours = message.text.split()
        code = code.upper()
        promos_db[code] = {
            "reward": int(reward),
            "max_uses": int(max_uses),
            "uses_left": int(max_uses),
            "expires_at": datetime.now() + timedelta(hours=int(hours))
        }
        await message.answer(f"✅ Промокод `{code}` создан! (Награда: {reward} ⭐, Лимит: {max_uses}, Срок: {hours}ч)", parse_mode="Markdown")
    except:
        await message.answer("⚠️ Формат: `/addpromo CODE 500 10 24`", parse_mode="Markdown")

@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    user_id = message.from_user.id
    users_db.setdefault(user_id, {"balance": 0, "used_promos": []})
    try:
        code = message.text.split()[1].upper()
    except:
        return await message.answer("ℹ️ Формат ввода: `/promo ТВОЙ_КОД`", parse_mode="Markdown")
    await message.answer(check_and_use_promo(user_id, code), parse_mode="Markdown")

def check_and_use_promo(user_id, code):
    if code not in promos_db: return "❌ Промокод не найден."
    promo = promos_db[code]
    if datetime.now() > promo["expires_at"]: return "⏳ Срок действия промокода истёк."
    if promo["uses_left"] <= 0: return "🚫 Лимит активаций промокода исчерпан."
    if code in users_db[user_id]["used_promos"]: return "⚠️ Вы уже активировали этот промокод!"
    
    promo["uses_left"] -= 1
    users_db[user_id]["used_promos"].append(code)
    users_db[user_id]["balance"] += promo["reward"]
    return f"🎉 Промокод `{code}` активирован! Начислено: +{promo['reward']} ⭐"

@dp.message(F.web_app_data)
async def receive_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "use_promo":
            res = check_and_use_promo(message.from_user.id, data.get("code", "").upper())
            await message.answer(res, parse_mode="Markdown")
    except:
        pass

if __name__ == "__main__":
    dp.run_polling(bot)
