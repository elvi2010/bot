import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

# ================== ХРАНИЛИЩА ==================
referrals = {}
used_users = set()
free_given = set()
given_accounts = set()
known_users = {}
messages_log = []
all_users = set()

# ================== КОНФИГУРАЦИЯ ==================
ADMIN_IDS = {7761934692}
TOKEN = os.getenv("BOT_TOKEN")  # <- токен берем из переменной окружения

# ================== Функции работы с аккаунтами ==================
def load_accounts_from(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def get_account_from_file(filename):
    global given_accounts
    accounts = load_accounts_from(file=filename)
    for acc in accounts:
        if acc not in given_accounts:
            given_accounts.add(acc)
            with open("given_accounts.txt", "a", encoding="utf-8") as f:
                f.write(acc + "\n")
            return acc
    return None

# ================== КЛАВИАТУРЫ ==================
def get_main_keyboard():
    keyboard = [
        ["🧾 Получить аккаунт"],
        ["🔗 Моя реферальная ссылка"],
        ["👨‍💻 ЛС разработчика"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_server_keyboard():
    return ReplyKeyboardMarkup([
        ["🇷🇺 Леста", "🌍 WG"],
        ["🔙 Назад"]
    ], resize_keyboard=True)

def get_lesta_keyboard():
    return ReplyKeyboardMarkup([
        ["🔥 Blitz (Леста)", "🛡 Мир Танков (Леста)"],
        ["🔙 Назад"]
    ], resize_keyboard=True)

def get_wg_keyboard():
    return ReplyKeyboardMarkup([
        ["🚀 Blitz (WG)", "⚔️ BB (WG)"],
        ["🔙 Назад"]
    ], resize_keyboard=True)

# ================== Функции команд ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username:
        known_users[user.username.lower()] = user.id
    all_users.add(user.id)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=get_main_keyboard())

async def handle_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    all_users.add(user)
    args = context.args
    if args:
        try:
            ref = int(args[0])
        except:
            ref = None
        if ref and ref != user and user not in used_users:
            used_users.add(user)
            referrals[ref] = referrals.get(ref, 0) + 1
            await update.message.reply_text("🎉 Спасибо за переход по реферальной ссылке!")
    await start(update, context)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
    if not context.args:
        return await update.message.reply_text("❗ Использование: /broadcast текст_сообщения")
    msg = " ".join(context.args)
    sent = 0
    for uid in all_users:
        try:
            await context.bot.send_message(uid, f"📢 *Объявление от администратора:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✔️ Сообщение отправлено {sent} пользователям.")

async def give_specific(update, context, game_name, filename):
    user = update.effective_user.id
    all_users.add(user)
    if user not in free_given:
        acc = get_account_from_file(filename)
        if acc:
            free_given.add(user)
            await update.message.reply_text(f"🎁 *Твой бесплатный аккаунт ({game_name}):*\n`{acc}`", parse_mode="Markdown", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text("⚠️ Аккаунты закончились.")
        return
    if referrals.get(user, 0) < 1:
        await update.message.reply_text("❌ У тебя нет рефералов.")
        return
    acc = get_account_from_file(filename)
    if not acc:
        await update.message.reply_text("⚠️ Аккаунты закончились.")
        return
    referrals[user] -= 1
    await update.message.reply_text(f"🎁 *Твой аккаунт за реферала ({game_name}):*\n`{acc}`", parse_mode="Markdown", reply_markup=get_main_keyboard())

async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери сервер:", reply_markup=get_server_keyboard())

async def send_ref_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={user}"
    await update.message.reply_text(f"🔗 Твоя реферальная ссылка:\n{link}")

async def dev_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍💻 ЛС разработчика:\n@NeinOfficial")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    all_users.add(user.id)
    messages_log.append((user.id, user.username, text))
    for admin_id in ADMIN_IDS:
        if user.id not in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, f"📩 Сообщение от @{user.username} ({user.id}):\n{text}")
            except:
                pass
    if text == "🧾 Получить аккаунт":
        await get_account(update, context)
        return
    if text == "🔗 Моя реферальная ссылка":
        await send_ref_link(update, context)
        return
    if text == "👨‍💻 ЛС разработчика":
        await dev_contact(update, context)
        return
    if text == "🔙 Назад":
        await update.message.reply_text("Вы вернулись в главное меню:", reply_markup=get_main_keyboard())
        return
    if text == "🇷🇺 Леста":
        await update.message.reply_text("Выбери игру:", reply_markup=get_lesta_keyboard())
        return
    if text == "🌍 WG":
        await update.message.reply_text("Выбери игру:", reply_markup=get_wg_keyboard())
        return
    if text == "🔥 Blitz (Леста)":
        await give_specific(update, context, "Blitz (Леста)", "lesta_blitz.txt")
        return
    if text == "🛡 Мир Танков (Леста)":
        await give_specific(update, context, "Мир Танков (Леста)", "lesta_wot.txt")
        return
    if text == "🚀 Blitz (WG)":
        await give_specific(update, context, "Blitz (WG)", "wg_blitz.txt")
        return
    if text == "⚔️ BB (WG)":
        await give_specific(update, context, "BB (WG)", "wg_bb.txt")
        return
    await update.message.reply_text("Выбери действие на клавиатуре.")

# ================== ЗАПУСК ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", handle_ref))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
