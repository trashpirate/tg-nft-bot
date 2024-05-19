import asyncio
import logging
from uuid import uuid4
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
from reflections import calcReflections, getBalanceOf


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def getReflections(address):
    reflections = calcReflections(address)
    text = "Reflections: {:,.2f} EARN".format(reflections)
    return text


def getBalance(address):
    balance = getBalanceOf(address)
    text = "Balance: {:,.2f} EARN".format(balance)
    return text


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
            reflect = getReflections(address)
            balance = getBalance(address)
            text = f"{balance}\n{reflect}"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter a valid wallet address.",
            )
    else:
        return


async def inline_reflections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.inline_query.query
    if not address:
        return
    if len(address) == 42 and address[:2] == "0x":
        reflect = getReflections(address)
        balance = getBalance(address)
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Reflections",
                input_message_content=InputTextMessageContent(reflect),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Balance",
                input_message_content=InputTextMessageContent(balance),
            ),
        ]
        await context.bot.answer_inline_query(update.inline_query.id, results)
    else:
        return


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main() -> None:

    # create bot
    application = ApplicationBuilder().token(TOKEN).build()

    # define handlers
    start_handler = CommandHandler("start", start)
    reflections_handler = CommandHandler("reflections", reflections)
    inline_reflections_handler = InlineQueryHandler(inline_reflections)

    # add commands
    application.add_handler(start_handler)
    application.add_handler(reflections_handler)
    application.add_handler(inline_reflections_handler)

    # run bot
    if URL == "":
        application.run_polling(poll_interval=5)
    else:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(PORT),
            url_path=TOKEN,
            webhook_url=URL + TOKEN,
        )


if __name__ == "__main__":
    main()
