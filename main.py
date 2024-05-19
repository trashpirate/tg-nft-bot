import asyncio
import logging
from uuid import uuid4
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    filters,
    ConversationHandler,
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

REFLECTIONS = range(1)


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
        chat_id=update.effective_chat.id,
        text="Enter wallet address to check reflections.",
    )
    return REFLECTIONS


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = " ".join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def reflections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
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
    return ConversationHandler.END


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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Use /reflections to check EARN reflections.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def main() -> None:

    # create bot
    application = ApplicationBuilder().token(TOKEN).build()

    # conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reflections", start)],
        states={
            REFLECTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflections)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # define handlers
    # start_handler = CommandHandler("start", start)
    # reflections_handler = CommandHandler("reflections", reflections)
    inline_reflections_handler = InlineQueryHandler(inline_reflections)

    # add commands
    # application.add_handler(start_handler)
    # application.add_handler(reflections_handler)
    application.add_handler(conv_handler)
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
