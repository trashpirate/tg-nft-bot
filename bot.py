from dataclasses import dataclass
import logging
from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
    CallbackQueryHandler,
    Application,
)
from web3 import Web3
from models import (
    CollectionConfigs,
    add_config,
    check_if_exists,
    db,
    query_table,
    update_config,
)
from credentials import ADMIN_ID, TABLE, TOKEN, URL
from graphql import create_webhook
from nfts import getCollectionInfo, getMetadata
from models import query_network_by_webhook

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# context
class ChatData:
    """Custom class for chat_data. Here we store data per message."""

    def __init__(self) -> None:
        self.webhook: str = None
        self.name: str = None
        self.network: str = None
        self.contract: str = None
        self.website: str = None
        self.chat: str = None


class CustomContext(CallbackContext[ExtBot, dict, ChatData, dict]):

    def __init__(
        self,
        application: Application,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self._message_id: Optional[int] = None

    @property
    def webhook(self) -> Optional[str]:
        return self.chat_data.webhook

    @property
    def network(self) -> Optional[str]:
        return self.chat_data.network

    @property
    def contract(self) -> Optional[str]:
        return self.chat_data.contract

    @property
    def website(self) -> Optional[str]:
        return self.chat_data.website

    @property
    def chat(self) -> Optional[str]:
        return self.chat_data.chat

    @webhook.setter
    def webhook(self, value: str) -> None:
        self.chat_data.webhook = value

    @network.setter
    def network(self, value: str) -> None:
        self.chat_data.network = value

    @contract.setter
    def contract(self, value: str) -> None:
        self.chat_data.contract = value

    @website.setter
    def website(self, value: str) -> None:
        self.chat_data.website = value

    @chat.setter
    def chat(self, value: str) -> None:
        self.chat_data.chat = value


# create bot
context_types = ContextTypes(context=CustomContext, chat_data=ChatData)
application = (
    ApplicationBuilder().token(TOKEN).updater(None).context_types(context_types).build()
)


# states
MAIN, NETWORK, CONTRACT, WEBSITE = range(4)
chat_ids = []
network_selected = ""
contract_address = ""


# keybords
def return_menu():
    keyboard = [
        [
            InlineKeyboardButton("RETURN", callback_data="return"),
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def main_menu():
    message_text = "CONFIG MENU"
    keyboard = [
        [
            InlineKeyboardButton("NEW CONFIG", callback_data="new"),
            InlineKeyboardButton("VIEW CONFIG", callback_data="view"),
        ],
        [
            InlineKeyboardButton("RETURN", callback_data="return"),
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ],
    ]
    return [InlineKeyboardMarkup(keyboard), message_text]


def network_menu():
    message_text = "Choose a Network:"
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="ethereum-mainnet"),
            InlineKeyboardButton("BASE", callback_data="base-mainnet"),
            InlineKeyboardButton("BNB", callback_data="bnbchain-mainnet"),
        ],
        [
            InlineKeyboardButton("Arbitrum", callback_data="arbitrum-mainnet"),
            InlineKeyboardButton("Avalanche", callback_data="avalanche-mainnet"),
            InlineKeyboardButton("Polygon", callback_data="polygon-mainnet"),
        ],
        [
            InlineKeyboardButton("RETURN", callback_data="return"),
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ],
    ]
    return [InlineKeyboardMarkup(keyboard), message_text]


# dataclasses
@dataclass
class WebhookUpdate:
    webhookId: str
    contract: str
    tokenId: object
    fromAddress: str
    toAddress: str
    hash: str
    type: str


# functions
async def parse_tx(json_data):

    # webhook id
    webhookId = json_data["metadata"]["stream_id"]
    print(webhookId)

    receipts = json_data["data"][0]["receipts"]
    if len(receipts) == 0:
        raise ValueError("No data available.")

    for receipt in receipts:

        for log in receipt["logs"]:
            # contract address
            contract = Web3.to_checksum_address(log["address"])
            # from address
            fromAddress = Web3.to_checksum_address("0x" + log["topics"][1][-40:])
            if fromAddress == "0x0000000000000000000000000000000000000000":
                txType = "mint"
            else:
                txType = "transfer"
            # owner address
            toAddress = Web3.to_checksum_address("0x" + log["topics"][2][-40:])
            # tokenId
            tokenId = int(log["topics"][3], 16)
            # transaction hash
            hash = log["transactionHash"]

            await application.update_queue.put(
                WebhookUpdate(
                    webhookId=webhookId,
                    tokenId=tokenId,
                    contract=contract,
                    fromAddress=fromAddress,
                    toAddress=toAddress,
                    hash=hash,
                    type=txType,
                )
            )


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    selected_option = query.data
    query.edit_message_text(text=f"You selected: {selected_option}")


async def start(update: Update, context: CustomContext):

    # webhookId = create_webhook(
    #     network="ethereum-mainnet",
    #     contract="0x12a961e8cc6c94ffd0ac08deb9cde798739cf775",
    #     filter="None",
    # )

    isPrivate = update.effective_chat.type == "private"
    if not isPrivate:
        admins = await update.effective_chat.get_administrators()
        admin_ids = [admin["user"]["id"] for admin in admins]

        if update.effective_user.id not in admin_ids:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are not authorized to configure this bot.",
            )
            return ConversationHandler.END

    [reply_markup, message_text] = main_menu()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=reply_markup,
    )
    return MAIN


async def select_action(update: Update, context: CustomContext):

    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Use /start to restart the bot."
        )
        return ConversationHandler.END

    if query.data == "return":
        [reply_markup, message_text] = main_menu()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup,
        )

        return MAIN

    if query.data == "view":
        rows = query_table(TABLE)

        message_text = ""
        index = 1
        for r in rows:
            message_text += f"Config {index}:\n{r[0]} ({r[2]})\n{r[1]}\n\n"
            index += 1

        reply_markup = return_menu()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup,
        )

        return MAIN

    if query.data == "new":
        context.chat = update.effective_chat.id
        chat_ids.append(update.effective_chat.id)

        [reply_markup, message_text] = network_menu()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup,
        )

    return NETWORK


async def select_network(update: Update, context: CustomContext):

    # print("added network")
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Use /start to restart the bot."
        )
        return ConversationHandler.END

    if query.data == "return":
        [reply_markup, message_text] = main_menu()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            reply_markup=reply_markup,
        )

        return MAIN

    context.network = query.data

    message_text = "Enter NFT Contract address:"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
    )

    return CONTRACT


async def enter_contract(update: Update, context: CustomContext):

    contract = update.message.text
    if len(contract) == 42 and contract[:2] == "0x":
        context.contract = contract
        message_text = "Enter your preferred website link (enter # to skip):"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
        )
        return WEBSITE

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter a valid wallet address:",
        )
        return CONTRACT


async def enter_website(update: Update, context: CustomContext):

    website = update.message.text
    if website == context.contract:
        return WEBSITE

    entry = await check_if_exists(context.network, context.contract)

    if entry is None:
        webhookId = create_webhook(
            network=context.network, contract=context.contract, filter="None"
        )
        [name, symbol] = await getCollectionInfo(context.network, context.contract)
        await add_config(
            name,
            context.network,
            context.contract,
            website,
            webhookId,
            [update.effective_chat.id],
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Collection is added."
        )

    else:
        await update_config(
            "Updated",
            context.network,
            context.contract,
            website,
            "some id",
            [update.effective_chat.id],
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Collection updated."
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
    [chats, network] = query_network_by_webhook(TABLE, update.webhookId)

    [img, text] = await getMetadata(
        update.contract, update.toAddress, update.tokenId, update.hash, network
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
            MAIN: [CallbackQueryHandler(select_action)],
            NETWORK: [CallbackQueryHandler(select_network)],
            CONTRACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contract)],
            WEBSITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_website)],
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
