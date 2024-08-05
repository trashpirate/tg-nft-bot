from dataclasses import dataclass
from http import HTTPStatus
import logging
from typing import Optional
import traceback


from flask import Response, request
from werkzeug.routing import Rule
from telegram import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    ChatMember,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Update,
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
from web3 import Web3
from models import (
    add_config,
    check_if_exists,
    delete_config_by_id,
    query_chats_by_contract,
    query_collection_by_chat,
    query_collection_by_id,
    query_collection_by_webhook,
    query_table,
    update_chats_by_id,
    update_config,
)
from credentials import TEST, TOKEN, URL
from graphql import create_test_webhook, create_webhook, delete_webhook
from nfts import getCollectionInfo, getMetadata, getSaleInfo, OPENSEA_NETWORK
from app import flask_app

# helpers
from helpers import NETWORK_SYMBOLS, RPC

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
        self.chat: int = None
        self.menu: int = None


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
    def chat(self) -> Optional[int]:
        return self.chat_data.chat

    @property
    def menu(self) -> Optional[int]:
        return self.chat_data.menu

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
    def chat(self, value: int) -> None:
        self.chat_data.chat = value

    @menu.setter
    def menu(self, value: int) -> None:
        self.chat_data.menu = value


#################################################################
#######################     WEBHOOK     #########################
#################################################################


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


# Function to dynamically create a new webhook route
def create_webhook_route(route):

    if route not in [rule.rule for rule in flask_app.url_map.iter_rules()]:

        flask_app.url_map.add(Rule(route, endpoint=route))

        # @flask_app.route(route, methods=["GET", "POST"])
        async def nft_updates() -> Response:
            json_data = request.json
            await update_webhook_queue(json_data)
            return Response(status=HTTPStatus.OK)

        flask_app.view_functions[route] = nft_updates
        print("Webhook route created: " + route)


# functions
def parse_tx(json_data):

    try:
        receipts = json_data["data"][0]["receipts"]
    except KeyError:
        try:
            receipts = json_data["data"]["receipts"]
        except Exception:
            traceback.print_exc()
            return None

    if len(receipts) < 1:
        # print("No new data.")
        return None

    # webhook id
    try:
        webhookId = json_data["metadata"]["stream_id"]
        network = json_data["metadata"]["network"]

        data = []
        for receipt in receipts:
            for log in receipt["logs"]:

                topics = log["topics"]
                if (
                    len(topics) == 4
                    and topics[0]
                    == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                ):
                    print(log)
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

                    # check if mint or purchase
                    if fromAddress != "0x0000000000000000000000000000000000000000":

                        info = getSaleInfo(network, contract, tokenId)
                        if info is None:
                            return None
                    else:
                        info = {
                            "type": "mint",
                            "price": "N/A",
                            "price_usd": "N/A",
                            "currency": "N/A",
                            "marketplace": "N/A",
                        }

                    data.append(
                        dict(
                            webhookId=webhookId,
                            tokenId=tokenId,
                            contract=contract,
                            fromAddress=fromAddress,
                            toAddress=toAddress,
                            hash=hash,
                            info=info,
                        )
                    )
        return data
    except Exception:
        traceback.print_exc()
        return None


#################################################################
#######################     BOT      ############################
#################################################################

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

# standard messages
cancel_message = "Use /start in group chat to restart the bot."
title_message = "*CONFIG MENU*\n\n"


# states
MAIN, NETWORK, CONTRACT, WEBSITE, ADD_CONFIG = range(5)
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
    message_text = title_message
    keyboard = [
        [
            InlineKeyboardButton("NEW CONFIG", callback_data="new"),
            InlineKeyboardButton("VIEW CONFIG", callback_data="view"),
        ],
        [
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ],
    ]
    return [InlineKeyboardMarkup(keyboard), message_text]


def network_menu():
    message_text = title_message
    message_text += "_Choose a Network:_"
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="ethereum-mainnet"),
            InlineKeyboardButton("BASE", callback_data="base-mainnet"),
            InlineKeyboardButton("BNB", callback_data="bnbchain-mainnet"),
        ],
        [
            InlineKeyboardButton("ARB", callback_data="arbitrum-mainnet"),
            InlineKeyboardButton("AVAX", callback_data="avalanche-mainnet"),
            InlineKeyboardButton("MATIC", callback_data="polygon-mainnet"),
        ],
        [
            InlineKeyboardButton("RETURN", callback_data="return"),
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ],
    ]
    return [InlineKeyboardMarkup(keyboard), message_text]


def bot_removed(update: Update, context: CallbackContext) -> None:
    # Extract the new and old status of the bot
    old_status = update.my_chat_member.old_chat_member.status
    new_status = update.my_chat_member.new_chat_member.status

    if old_status in [ChatMember.ADMINISTRATOR, ChatMember.MEMBER] and (
        new_status == ChatMember.BANNED or new_status == ChatMember.LEFT
    ):

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


async def webhook_update(
    update: WebhookUpdate, context: ContextTypes.DEFAULT_TYPE
) -> None:

    data_list = parse_tx(update.data)
    if data_list is None or len(data_list) == 0:
        return

    for data in data_list:
        collection = query_collection_by_webhook(data["webhookId"])
        network = collection["network"]

        [img, text] = getMetadata(
            network,
            data["contract"],
            data["toAddress"],
            data["tokenId"],
            data["hash"],
            data["info"],
        )

        chats: list[str] = collection["chats"]
        for chat_id in chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    link_preview_options=LinkPreviewOptions(
                        url=img, show_above_text=True
                    ),
                    parse_mode="HTML",
                )

            except Exception as e:
                print("Sending message failed:")
                traceback.print_exc()
                return


async def update_queue(new_data):
    await application.update_queue.put(
        Update.de_json(data=new_data, bot=application.bot)
    )


async def update_webhook_queue(new_data):
    await application.update_queue.put(WebhookUpdate(data=new_data))


async def enter_website(update: Update, context: CustomContext):

    query = update.callback_query

    if query is not None:
        await query.answer()
        if query.data == "cancel":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=cancel_message,
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END

        if query.data == "return":
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "_Enter NFT Contract address:_\n\n"
            reply_markup = return_menu()

            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            return CONTRACT

    else:
        website = update.message.text

        user_message = update.message
        await user_message.delete()

        if website == context.contract:
            return WEBSITE

        try:
            [name, slug] = getCollectionInfo(context.network, context.contract)

            if website[:8] != "https://":
                website = (
                    "https://opensea.io/assets/"
                    + OPENSEA_NETWORK[context.network]
                    + "/"
                    + context.contract
                )

            route = "/" + slug
            create_webhook_route(route)

            if TEST == "true":
                webhookId = create_test_webhook(
                    network=context.network, contract=context.contract, route=route
                )

            entry = check_if_exists(context.network, context.contract)
            webhookId = create_webhook(
                network=context.network, contract=context.contract, route=route
            )

            if entry is None:
                # TODO:
                # check if contract exists

                add_config(
                    name,
                    slug,
                    context.network,
                    context.contract,
                    website,
                    webhookId,
                    [context.chat],
                )
                status = "_Collection is added._"
            else:

                chats: list[str] = query_chats_by_contract(
                    context.network, context.contract
                )

                exist_count = chats.count(context.chat)
                if exist_count == 0:
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

                status = "_Collection is updated._"
        except Exception:
            traceback.print_exc()
            status = "_Configuration failed. Please start over and try again._"

        message_text = title_message
        message_text += (
            "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
        )
        message_text += "Contract Address: *" + context.contract + "*\n\n"
        message_text += "Website: *" + website + "*\n\n"
        message_text += status
        reply_markup = return_menu()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=message_text,
            message_id=context.menu,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )
        return MAIN


async def enter_contract(update: Update, context: CustomContext):

    query = update.callback_query

    if query is not None:
        await query.answer()
        if query.data == "cancel":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=cancel_message,
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END

        if query.data == "return":
            [reply_markup, message_text] = network_menu()

            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            return NETWORK

    # process text entry
    else:

        contract = update.message.text

        user_message = update.message
        await user_message.delete()

        if contract is not None and len(contract) == 42 and contract[:2] == "0x":
            context.contract = contract
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "Contract Address: *" + contract + "*\n\n"
            message_text += "_Enter your main collection website (e.g. https://mintingsite.com, enter # to skip):_\n\n"
            reply_markup = return_menu()

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                text=message_text,
                message_id=context.menu,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            return WEBSITE

        else:
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "Contract Address: *" + contract + "*\n\n"
            message_text += "_Please enter a valid wallet address:_\n\n"
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.menu,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
            )
            return CONTRACT


async def select_network(update: Update, context: CustomContext):

    # print("added network")
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=cancel_message,
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    if query.data == "return":
        [reply_markup, message_text] = main_menu()

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        return MAIN

    context.network = query.data

    message_text = title_message
    message_text += "Selected Network: *" + NETWORK_SYMBOLS[query.data] + "*\n\n"
    message_text += "_Enter NFT Contract address:_\n\n"
    reply_markup = return_menu()
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )

    return CONTRACT


async def select_action(update: Update, context: CustomContext):

    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=cancel_message,
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    if query.data == "return":
        [reply_markup, message_text] = main_menu()

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        return MAIN

    if query.data == "view":

        try:
            message_text = "<b>BOT CONFIGURATIONS:</b>\n\n"
            index = 1
            config_buttons = []
            rows: list[dict] = query_table()
            if len(rows) == 0:
                message_text = "No collections configured."
            else:
                for r in rows:
                    cid = r["id"]
                    name = r["name"]
                    network = r["network"]
                    contract = r["contract"]
                    website = r["website"]
                    chats = r["chats"]

                    chats_isAdmin = []
                    for chat in chats:
                        admins = await application.bot.get_chat_administrators(chat)
                        admin_ids = [admin["user"]["id"] for admin in admins]
                        if update.effective_user.id in admin_ids:
                            chats_isAdmin.append(chat)

                    # throw exception if user is not admin in any of the configured groups
                    if len(chats_isAdmin) == 0:
                        raise Exception("User is not admin of any configurations.")

                    if len(r["website"]) > 8:
                        website = r["website"]
                    else:
                        website = "https://opensea.io/collection/" + r["slug"]

                    message_text += f"<u><b>CONFIG {index}:</b></u>\nName: {name}\nNetwork: {NETWORK_SYMBOLS[network]}\nCA: {contract}\nWebsite: {website}\nChats: "

                    for chat in chats_isAdmin:
                        group_chat = await context.bot.get_chat(chat)
                        if group_chat.title is None:
                            chat_name = group_chat.username
                        else:
                            chat_name = group_chat.title
                        message_text += chat_name + ", "

                    message_text = message_text[:-2] + "\n\n"

                    row_buttons = [
                        InlineKeyboardButton(
                            "ADD CONFIG " + str(index), callback_data="add-" + str(cid)
                        ),
                        InlineKeyboardButton(
                            "DELETE CONFIG " + str(index),
                            callback_data="del-" + str(cid),
                        ),
                    ]
                    config_buttons.append(row_buttons)
                    index += 1

            config_buttons.append(
                [
                    InlineKeyboardButton("RETURN", callback_data="return"),
                    InlineKeyboardButton("CANCEL", callback_data="cancel"),
                ]
            )

            reply_markup = InlineKeyboardMarkup(config_buttons)

            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )

            return ADD_CONFIG

        except Exception:
            traceback.print_exc()
            reply_markup = return_menu()
            await query.edit_message_text(
                text="No configurations found.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            return MAIN

    if query.data == "new":
        [reply_markup, message_text] = network_menu()

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    return NETWORK


async def add_collection(update: Update, context: CustomContext):

    query = update.callback_query
    await query.answer()

    await query.answer()
    if query.data == "cancel":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=cancel_message,
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    if query.data == "return":
        [reply_markup, message_text] = main_menu()

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        return MAIN

    if query.data[:3] == "add":
        collection = query_collection_by_id(int(query.data[4:]))
        chats: list[int] = collection["chats"]

        exist_count = chats.count(context.chat)
        if exist_count == 0:
            chats.append(context.chat)

            update_config(
                collection["name"],
                collection["slug"],
                collection["network"],
                collection["contract"],
                collection["website"],
                collection["webhookId"],
                chats,
            )

            name = collection["name"]
            status = f"<i>{name} collection added.</i>"
        else:
            name = collection["name"]
            status = f"<i>{name} collection aready added.</i>"

    if query.data[:3] == "del":
        collection = query_collection_by_id(int(query.data[4:]))

        if len(collection["chats"]) == 1 and collection["chats"][0] == context.chat:
            name = collection["name"]
            delete_webhook(collection["webhookId"])
            delete_config_by_id(collection["id"])

            status = f"<i>{name} collection removed from group chat.</i>"
        else:
            new_chats = []
            for chat in collection["chats"]:
                if chat != context.chat:
                    new_chats.append(chat)

            update_chats_by_id(collection["id"], new_chats)
            name = collection["name"]
            status = f"<i>{name} collection removed.</i>"
    try:
        message_text = "<b>BOT CONFIGURATIONS:</b>\n\n"
        index = 1
        row_buttons = []
        config_buttons = []
        rows: list[dict] = query_table()
        print(rows)
        for r in rows:
            cid = r["id"]
            name = r["name"]
            network = r["network"]
            contract = r["contract"]
            website = r["website"]
            chats = r["chats"]

            chats_isAdmin = []
            for chat in chats:
                admins = await application.bot.get_chat_administrators(chat)
                admin_ids = [admin["user"]["id"] for admin in admins]
                if update.effective_user.id in admin_ids:
                    chats_isAdmin.append(chat)

            # throw exception if user is not admin in any of the configured groups
            if len(chats_isAdmin) == 0:
                raise Exception("User is not admin of any configurations.")

            if len(r["website"]) > 8:
                website = r["website"]
            else:
                website = "https://opensea.io/collection/" + r["slug"]

            message_text += f"<u><b>CONFIG {index}:</b></u>\nName: {name}\nNetwork: {NETWORK_SYMBOLS[network]}\nCA: {contract}\nWebsite: {website}\nChats: "

            for chat in chats_isAdmin:
                group_chat = await context.bot.get_chat(chat)
                if group_chat.title is None:
                    chat_name = group_chat.username
                else:
                    chat_name = group_chat.title
                message_text += chat_name + ", "

            message_text = message_text[:-2] + "\n\n"

            row_buttons = [
                InlineKeyboardButton(
                    "ADD CONFIG " + str(index), callback_data="add-" + str(cid)
                ),
                InlineKeyboardButton(
                    "DELETE CONFIG " + str(index), callback_data="del-" + str(cid)
                ),
            ]
            config_buttons.append(row_buttons)

            index += 1

        message_text += status
        config_buttons.append(
            [
                InlineKeyboardButton("RETURN", callback_data="return"),
                InlineKeyboardButton("CANCEL", callback_data="cancel"),
            ]
        )

        reply_markup = InlineKeyboardMarkup(config_buttons)

        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

        return ADD_CONFIG

    except Exception:
        traceback.print_exc()
        reply_markup = return_menu()
        await query.edit_message_text(
            text="No configurations found.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        return MAIN


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
                parse_mode=ParseMode.MARKDOWN,
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
            context.chat = int(context.args[0])
            [reply_markup, message_text] = main_menu()
            message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )
            context.menu = message.message_id
            return MAIN
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="To configure the bot, start the bot in the group where you want to configure it and click on the link in the group message.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Use /start in the group chat to restart the bot.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )

    return ConversationHandler.END


async def start_app():

    # conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [CallbackQueryHandler(select_action)],
            NETWORK: [CallbackQueryHandler(select_network)],
            CONTRACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contract),
                CallbackQueryHandler(enter_contract),
            ],
            WEBSITE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_website),
                CallbackQueryHandler(enter_website),
            ],
            ADD_CONFIG: [CallbackQueryHandler(add_collection)],
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

    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("cancel", "Cancel the current operation"),
        # Add other commands here
    ]
    await application.bot.set_my_commands(
        commands, scope=BotCommandScopeAllChatAdministrators()
    )

    # webhooks
    await application.bot.set_webhook(
        url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES
    )

    return application
