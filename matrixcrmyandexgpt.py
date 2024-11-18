import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters

# Настройки YandexGPT
IAM_TOKEN = "t1.9euelZrMjpuamomWkJrHmcmQj5aKx-3rnpWanY6Uz8-Ylp6Zmo3PlJ2Wj5Xl8_cFLRNG-e98GWps_d3z90VbEEb573wZamz9zef1656VmpudzJaUx57Gj5aSkpzGzs-e7_zF656VmpudzJaUx57Gj5aSkpzGzs-e.68etj397uGUg1HUsZB3hAmLtjYrZMo0t0VssRdqQgcs-UaXxQWsm1xeRKBKapN_iaw9ePxrNP5V4GLMKn64bDw"
CATALOG_ID = "b1gb9k14k5ui80g91tnp"
MODEL_URI = f"gpt://{CATALOG_ID}/yandexgpt/rc"

# Телеграм токен
TELEGRAM_TOKEN = "7828823061:AAFqiiM3bQhB2Ab1hidTMXaziGDCps5H3N4"

# Функция для генерации текста с использованием YandexGPT
def generate_text(user_description):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IAM_TOKEN}"
    }
    prompt = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "system",
                "text": (
                    "Ты помощник компании MatrixCRM. Твоя задача — создавать текстовые описания обновлений CRM-системы. "
                    "Сообщения должны быть объёмными, детализированными и полезными. "
                    "Каждое сообщение должно начинаться с яркого заголовка с эмодзи, привлекающим внимание, например: '🚀 Обновление Matrix CRM!'. "
                    "Далее идёт краткое введение, поясняющее, что это за обновление и как оно улучшает работу пользователей. "
                    "После этого перечисляются все ключевые изменения в виде списка. Каждый пункт должен сопровождаться тематическим смайлом, "
                    "а также содержать подробное описание и пример использования новой функции. "
                    "Сообщение завершается позитивным заключением, вдохновляющим пользователей продолжать пользоваться MatrixCRM. "
                    "В конце каждого поста обязательно добавляй хэштеги: #MatrixCRM #Обновления #УправлениеКлиентами #Эффективность."
                )
            },
            {
                "role": "user",
                "text": user_description
            }
        ]
    }
    response = requests.post(url, headers=headers, json=prompt)
    if response.status_code == 200:
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    else:
        return f"Ошибка {response.status_code}: {response.text}"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите краткое описание обновлений для CRM:")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_description = update.message.text
    await update.message.reply_text("Генерирую текст для публикации...")
    generated_text = generate_text(user_description)
    keyboard = [
        [InlineKeyboardButton("Утвердить", callback_data="approve")],
        [InlineKeyboardButton("Регенерировать", callback_data="regenerate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data["last_description"] = user_description
    context.user_data["generated_text"] = generated_text
    await update.message.reply_text(f"Сгенерированный текст:\n\n{generated_text}", reply_markup=reply_markup)

# Обработчик кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "approve":
        await query.edit_message_text(f"✅ Текст утверждён:\n\n{context.user_data['generated_text']}")
    elif query.data == "regenerate":
        await query.edit_message_text("Введите новый текст для регенерации:")
        context.user_data["waiting_for_regeneration"] = True

# Обработчик текстов для регенерации
async def regenerate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_regeneration"):
        user_description = update.message.text
        await update.message.reply_text("Регенерирую текст...")
        generated_text = generate_text(user_description)
        keyboard = [
            [InlineKeyboardButton("Утвердить", callback_data="approve")],
            [InlineKeyboardButton("Регенерировать", callback_data="regenerate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data["generated_text"] = generated_text
        context.user_data["waiting_for_regeneration"] = False
        await update.message.reply_text(f"Сгенерированный текст:\n\n{generated_text}", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Я не жду текстового ввода. Используйте /send для начала.")

# Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, regenerate_message))

    app.run_polling()

if __name__ == "__main__":
    main()
