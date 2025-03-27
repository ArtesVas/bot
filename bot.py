import random
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import asyncio

TOKEN = "7980357006:AAH8jc9_f29f-KD6PmZgT6g5xDzIlFeXv-Q"  # Токен сюда

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Игры, по которым ищем популярные товары
GAMES = {
    "genshin": "https://playerok.com/games/genshin-impact/coins",
    "steam": "https://playerok.com/apps/steam/top-up",
    "pubg": "https://playerok.com/mobile-games/pubg-mobile/coins",
    "freefire": "https://playerok.com/mobile-games/free-fire/coins",
}

# Кешированные данные для обновления каждые 5 минут
CACHED_ITEMS = {}

# Функция парсинга популярных товаров с защитой от блокировок
def get_popular_items(game):
    url = GAMES.get(game)
    if not url:
        return "❌ Игра не найдена!"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "❌ Ошибка при получении данных."
    
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    
    for item in soup.find_all("div", class_="product-card"):  # Класс карточки товара
        try:
            name = item.find("h3").text.strip()
            orders = int(item.find("span", class_="orders-count").text.strip().split()[0])
            price = float(item.find("span", class_="price").text.strip().replace("₽", ""))
            link = item.find("a")["href"]
            
            if orders < 5:
                status = "🚫 Не ликвид (мало заказов)"
            else:
                price_competitive = price + random.randint(2, 5)
                status = f"✅ Конкурентная цена: {price_competitive}₽"
            
            items.append({
                "name": name,
                "orders": orders,
                "price": price,
                "link": "https://playerok.com" + link,
                "status": status
            })
        except AttributeError:
            continue  # Пропускаем, если элемент не найден
    
    return items

# Фоновое обновление данных каждые 5 минут
async def update_cache():
    global CACHED_ITEMS
    while True:
        for game in GAMES.keys():
            CACHED_ITEMS[game] = get_popular_items(game)
        await asyncio.sleep(300)  # 5 минут

# Команда /popular для поиска популярных товаров
@dp.message_handler(commands=["popular"])
async def send_popular_items(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Укажите игру! Например: /popular pubg")
        return
    
    game = args[1].lower()
    items = CACHED_ITEMS.get(game, "❌ Данные ещё не загружены. Попробуйте позже.")
    
    if isinstance(items, str):
        await message.reply(items)
        return
    
    response = f"🔥 Популярные товары в {game.capitalize()}:\n\n"
    for item in items[:5]:  # Выводим только топ-5
        response += f"🔹 {item['name']}\n💰 Цена: {item['price']}₽\n📦 Заказы: {item['orders']}\n{item['status']}\n🔗 [Ссылка]({item['link']})\n\n"
    
    await message.reply(response, parse_mode="Markdown")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(update_cache())
    executor.start_polling(dp, skip_updates=True)
input("Нажмите Enter, чтобы выйти...")  # Добавь эту строчку в конце кода