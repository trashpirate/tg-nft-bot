from dataclasses import dataclass
import logging
from typing import Optional

from telegram import (
    ChatMember,
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
    ChatMemberHandler,
    CallbackContext,
    ExtBot,
    TypeHandler,
    CallbackQueryHandler,
    Application,
)
from web3 import HTTPProvider, Web3
from models import (
    add_config,
    check_if_exists,
    delete_config_by_id,
    query_chats_by_contract,
    query_collection_by_chat,
    query_collection_by_webhook,
    query_table,
    update_chats_by_id,
    update_config,
)
from credentials import TEST, TOKEN, URL
from graphql import RPC, create_test_webhook, create_webhook, delete_webhook
from nfts import getCollectionInfo, getMetadata

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
    ApplicationBuilder()
    .token(TOKEN)
    .updater(None)
    .context_types(context_types)
    .concurrent_updates(True)
    .build()
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
    data: str


class WebhookData:
    webhookId: str
    contract: str
    tokenId: object
    fromAddress: str
    toAddress: str
    hash: str
    type: str
    value: float


# functions
def parse_tx(json_data):

    receipts = json_data["data"][0]["content"]["receipts"]

    if len(receipts) < 1:
        print("No new data.")
        return None

    # webhook id
    webhookId = json_data["metadata"]["stream_id"]
    network = json_data["metadata"]["network"]

    for receipt in receipts:
        for log in receipt["logs"]:

            topics = log["topics"]
            if (
                len(topics) == 4
                and topics[0]
                == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            ):

                # contract address
                contract = Web3.to_checksum_address(log["address"])
                # from address
                fromAddress = Web3.to_checksum_address("0x" + topics[1][-40:])
                # owner address
                toAddress = Web3.to_checksum_address("0x" + topics[2][-40:])
                # tokenId
                tokenId = int(topics[3], 16)
                # transaction hash
                hash = log["transactionHash"]
                # eth value
                value = 0

                # check if mint or purchase
                if fromAddress == "0x0000000000000000000000000000000000000000":
                    txType = "mint"
                else:

                    w3 = Web3(HTTPProvider(RPC[network]))
                    tx = w3.eth.get_transaction(hash)
                    value = Web3.from_wei(tx["value"], "ether")
                    if value > 0:
                        txType = "purchase"
                    else:
                        return None

                return dict(
                    webhookId=webhookId,
                    tokenId=tokenId,
                    contract=contract,
                    fromAddress=fromAddress,
                    toAddress=toAddress,
                    hash=hash,
                    type=txType,
                    value=value,
                )


def bot_removed(update: Update, context: CallbackContext) -> None:
    # Extract the new and old status of the bot
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status

    if old_status in [ChatMember.ADMINISTRATOR, ChatMember.MEMBER] and (
        new_status == ChatMember.BANNED or new_status == ChatMember.LEFT
    ):
        # TODO:
        # delete webhook if no chat left
        collections = query_collection_by_chat(update.effective_chat.id)

        for collection in collections:
            new_chats = []
            if (
                len(collection["chats"]) == 1
                and collection["chats"][0] == update.effective_chat.id
            ):
                # delete webhook
                # delete db entry
                delete_webhook(collection["webhookId"])
                delete_config_by_id(collection["id"])
            else:
                for chat in collection["chats"]:
                    if chat != update.effective_chat.id:
                        new_chats.append(chat)

                update_chats_by_id(collection["id"], new_chats)


async def start(update: Update, context: CustomContext):

    if (
        update.effective_chat.type == "group"
        or update.effective_chat.type == "supergroup"
    ):
        admins = await update.effective_chat.get_administrators()
        admin_ids = [admin["user"]["id"] for admin in admins]

        if update.effective_user.id not in admin_ids:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are not authorized to configure this bot.",
            )
            return ConversationHandler.END
        else:
            group_chat_id = update.effective_chat.id
            bot_username = context.bot.username
            message = (
                "To configure bot: "
                f"[Click here](https://t.me/{bot_username}?start={group_chat_id})"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
            )

    elif update.effective_chat.type == "private":
        if context.args:
            context.chat = context.args[0]
            [reply_markup, message_text] = main_menu()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=reply_markup,
            )
            return MAIN
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="To configure the bot, start the bot in the group where you want to configure it and click on the link in the group message.",
            )
            return ConversationHandler.END


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
        rows: list[dict] = query_table()

        if len(rows) > 0:
            message_text = ""
            index = 1
            for r in rows:
                name = r["name"]
                network = r["network"]
                contract = r["contract"]
                website = r["website"]
                chats = r["chats"]

                message_text += f"Config {index}:\nName: {name}\nNetwork: {network}\nCA: {contract}\nWebsite: {website}\nChats: "

                for chat in chats:
                    group_chat = await context.bot.get_chat(chat)
                    if group_chat.title is None:
                        chat_name = group_chat.username
                    else:
                        chat_name = group_chat.title
                    message_text += chat_name + ", "

                message_text = message_text[:-2] + "\n\n"
                index += 1

            reply_markup = return_menu()

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=reply_markup,
            )

        else:
            reply_markup = return_menu()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No configurations found.",
                reply_markup=reply_markup,
            )

        return MAIN

    if query.data == "new":
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

    print(TEST)
    if TEST == "true":
        webhookId = create_test_webhook(
            network=context.network, contract=context.contract
        )

    entry = check_if_exists(context.network, context.contract)

    if entry is None:
        # TODO:
        # check if contract exists

        webhookId = create_webhook(network=context.network, contract=context.contract)
        [name, slug] = getCollectionInfo(context.network, context.contract)

        add_config(
            name,
            slug,
            context.network,
            context.contract,
            website,
            webhookId,
            [context.chat],
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Collection is added."
        )

    else:
        webhookId = create_webhook(network=context.network, contract=context.contract)

        [name, slug] = getCollectionInfo(context.network, context.contract)
        chats: list[str] = query_chats_by_contract(context.network, context.contract)
        if context.chat not in chats:
            chats.append(context.chat)

        update_config(
            name,
            slug,
            context.network,
            context.contract,
            website,
            webhookId,
            chats,
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

    data = parse_tx(update.data)
    if data is None:
        return

    collection = query_collection_by_webhook(data["webhookId"])
    network = collection["network"]

    [img, text] = getMetadata(
        network,
        data["contract"],
        data["toAddress"],
        data["tokenId"],
        data["hash"],
        data["type"],
        data["value"],
    )

    chats: list[str] = collection["chats"]
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


async def update_webhook_queue(new_data):
    await application.update_queue.put(WebhookUpdate(data=new_data))


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
    application.add_handler(conv_handler)
    application.add_handler(
        TypeHandler(type=WebhookUpdate, callback=webhook_update, block=False)
    )
    application.add_handler(
        ChatMemberHandler(bot_removed, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    # webhooks
    await application.bot.set_webhook(
        url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES
    )

    return application
