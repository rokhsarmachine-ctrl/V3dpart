import asyncio
import sqlite3
import datetime
import os

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup

# ---------------- CONFIG ----------------
API_TOKEN = "8845237405:AAGtafV4_peE4i_y7w31hMa-lWhKunFWWV8"
ADMIN_ID =  7122529232  # آیدی خودت

# ---------------- DATABASE ----------------
conn = sqlite3.connect("orders.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    phone TEXT,
    description TEXT,
    file_path TEXT,
    date TEXT
)
""")
conn.commit()

# ---------------- STATES ----------------
class OrderState(StatesGroup):
    name = State()
    phone = State()
    description = State()
    file = State()

# ---------------- BOT ----------------
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ---------------- START ----------------
@dp.message(commands=["start"])
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🧩 ثبت سفارش طراحی سه‌بعدی")

    await msg.answer(
        "سلام! برای ثبت سفارش طراحی سه‌بعدی قطعه، روی گزینه زیر کلیک کن.",
        reply_markup=kb
    )

# ---------------- ORDER ----------------
@dp.message(lambda m: m.text == "🧩 ثبت سفارش طراحی سه‌بعدی")
async def order_start(msg: types.Message, state: FSMContext):
    await msg.answer("نام و نام خانوادگی خود را وارد کنید:")
    await state.set_state(OrderState.name)

@dp.message(OrderState.name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("شماره تماس خود را وارد کنید:")
    await state.set_state(OrderState.phone)

@dp.message(OrderState.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await msg.answer("توضیحات قطعه را ارسال کنید:")
    await state.set_state(OrderState.description)

@dp.message(OrderState.description)
async def get_description(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await msg.answer("اگر فایل یا عکس قطعه دارید، ارسال کنید.\nاگر ندارید، بنویسید: «ندارم»")
    await state.set_state(OrderState.file)

@dp.message(OrderState.file, content_types=['document', 'photo', 'text'])
async def get_file(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    file_path = "NO_FILE"

    if msg.document:
        file = msg.document
        file_path = f"files/{file.file_name}"
        await file.download(file_path)

    elif msg.photo:
        photo = msg.photo[-1]
        file_path = f"files/{photo.file_id}.jpg"
        await photo.download(file_path)

    cur.execute("""
        INSERT INTO orders(user_id, name, phone, description, file_path, date)
        VALUES(?,?,?,?,?,?)
    """, (
        msg.from_user.id,
        data["name"],
        data["phone"],
        data["description"],
        file_path,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()

    await msg.answer("سفارش شما با موفقیت ثبت شد. تا چند ساعت آینده با شما تماس گرفته می‌شود.")
    await state.clear()

# ---------------- ADMIN PANEL ----------------
@dp.message(commands=["admin"])
async def admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return

    await msg.answer("📋 لیست سفارش‌ها:")

    cur.execute("SELECT id, name, phone, description, file_path, date FROM orders")
    rows = cur.fetchall()

    if not rows:
        await msg.answer("هیچ سفارشی ثبت نشده.")
        return

    for r in rows:
        order_id, name, phone, desc, file_path, date = r
        text = (
            f"🆔 سفارش: {order_id}\n"
            f"👤 نام: {name}\n"
            f"📞 تماس: {phone}\n"
            f"📄 توضیحات: {desc}\n"
            f"📅 تاریخ: {date}\n"
        )

        await msg.answer(text)

        if file_path != "NO_FILE":
            try:
                await msg.answer_document(open(file_path, "rb"))
            except:
                await msg.answer("❗ فایل قابل ارسال نیست.")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not os.path.exists("files"):
        os.mkdir("files")
    asyncio.run(main())
