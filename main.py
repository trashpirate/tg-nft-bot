import asyncio
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)


from credentials import TOKEN, PORT, URL
from reflections import calcReflections


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = " ".join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def reflections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) == 1:
        address = context.args[0]
        if len(address) == 42 and address[:2] == "0x":
            reflections = calcReflections(address)
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text='Your reflections: {:,.2f} EARN'.format(reflections)
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter a valid wallet address.",
            )

async def inline_reflections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    reflections = calcReflections(query)

    results = []
    results.append(
        InlineQueryResultArticle(
            id=query,
            title="Reflections",
            input_message_content=InputTextMessageContent(f"{reflections} EARN"),
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


if __name__ == "__main__":

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)
    reflections_handler = CommandHandler("reflections", reflections)
    inline_reflections_handler = InlineQueryHandler(inline_reflections)

    application.add_handler(start_handler)
    application.add_handler(reflections_handler)
    application.add_handler(inline_reflections_handler)

    # application.run_polling(allowed_updates=Update.ALL_TYPES)
    if URL == "":
        application.run_polling(poll_interval=5)
    else:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(PORT),
            url_path=TOKEN,
            webhook_url=URL + TOKEN,
        )
