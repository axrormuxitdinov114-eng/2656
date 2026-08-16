import asyncio
import os
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from config import BOT_TOKEN
from database import db
from handlers import router

app = Flask(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="admin", description="Admin panel"),
    ]
    await bot.set_my_commands(commands)

async def start_bot():
    await db.init_db()
    dp.include_router(router)
    await set_bot_commands()
    print("Bot started! 🚀")
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(start_bot())

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)