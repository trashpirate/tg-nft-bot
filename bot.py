from dataclasses import dataclass
import logging

from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    filters,
    ConversationHandler,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    CallbackContext,
    ExtBot,
    TypeHandler,
)
from web3 import Web3

from credentials import ADMIN_ID, TOKEN, URL
from graphql import create_webhook
from nfts import getMetadata
from models import query_network_by_webhook

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# create bot
application = ApplicationBuilder().token(TOKEN).build()

NETWORK, CONTRACT, FILTER = range(3)
chat_ids = []
network_selected = ""
contract_address = ""


@dataclass
class WebhookUpdate:
    webhookId: str
    contract: str
    tokenId: object
    fromAddress: str
    toAddress: str
    hash: str


async def parse_tx(json_data):
    logs = json_data["event"]["data"]["block"]["logs"]

    if len(logs) == 0:
        raise ValueError("No data available.")

    # webhook id
    webhookId = json_data["webhookId"]

    for log in logs:
        # contract address
        contract = Web3.to_checksum_address(log["account"]["address"])
        # tokenId
        tokenId = int(log["topics"][3], 16)
        # owner address
        toAddress = Web3.to_checksum_address("0x" + log["topics"][2][-40:])
        # owner address
        fromAddress = Web3.to_checksum_address("0x" + log["topics"][1][-40:])
        # transaction hash
        hash = log["transaction"]["hash"]

        await application.update_queue.put(
            WebhookUpdate(
                webhookId=webhookId,
                tokenId=tokenId,
                contract=contract,
                fromAddress=fromAddress,
                toAddress=toAddress,
                hash=hash,
            )
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Chat id: {update.effective_chat.id}")
    if update.effective_user.id == int(ADMIN_ID):
        chat_ids.append(update.effective_chat.id)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Enter Network:"
        )
        return NETWORK
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not authorized to configure this bot.",
        )


async def add_network(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global network_selected
    network_selected = update.message.text
    print("added network")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Enter NFT Contract address:"
    )
    return CONTRACT


async def add_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contract = update.message.text

    if len(contract) == 42 and contract[:2] == "0x":
        global contract_address
        contract_address = contract
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Enter a block filter (only testing):",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter a valid wallet address.",
        )
    return FILTER


async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filter = update.message.text

    global network_selected
    global contract_address
    create_webhook(network=network_selected, contract=contract_address, filter=filter)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Webhook created."
    )
    return ConversationHandler.END


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
        "Use /start to restart the bot.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def webhook_update(
    update: WebhookUpdate, context: ContextTypes.DEFAULT_TYPE
) -> None:
    [chats, network] = query_network_by_webhook("collections", update.webhookId)

    if network == "ETH_MAINNET":
        [img, text] = getMetadata(
            update.contract, update.toAddress, update.tokenId, update.hash, "ethereum"
        )
        for chat_id in chats:
            try:
                await context.bot.send_photo(
                    chat_id=chat_id, photo=img, caption=text, parse_mode="HTML"
                )
            except:
                print("Sending message failed")
                return

    elif network == "BASE_MAINNET":
        [img, text] = getMetadata(
            update.contract, update.toAddress, update.tokenId, update.hash, "base"
        )

        for chat_id in chats:
            try:
                await context.bot.send_photo(
                    chat_id=chat_id, photo=img, caption=text, parse_mode="HTML"
                )
            except:
                print("Sending message failed")
                return


async def update_queue(new_data):
    await application.update_queue.put(
        Update.de_json(data=new_data, bot=application.bot)
    )


async def start_app():

    # conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NETWORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_network)],
            CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_contract)],
            FILTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_filter)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # define handlers
    # start_handler = CommandHandler("start", start)
    # webhook_handler = CommandHandler("webhook", webhook)

    # add commands
    # application.add_handler(start_handler)
    # application.add_handler(webhook_handler)
    application.add_handler(conv_handler)
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))

    # webhooks
    await application.bot.set_webhook(
        url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES
    )

    return application
