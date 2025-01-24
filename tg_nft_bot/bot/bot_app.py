import logging
import traceback

from telegram import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    ChatMember,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    filters,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
    CallbackContext,
    TypeHandler,
    CallbackQueryHandler,
)
from tronpy import Tron
from web3 import Web3
from tg_nft_bot.bot.bot_utils import CustomContext, WebhookUpdate, create_webhook_route
from tg_nft_bot.db.db_operations import (
    add_config,
    check_if_exists,
    delete_config_by_id,
    query_chats_by_contract,
    query_collection_by_chat,
    query_collection_by_id,
    query_table,
    update_chats_by_id,
    update_config,
)

# helpers
from tg_nft_bot.utils.addresses import get_hex_address, is_address
from tg_nft_bot.utils.networks import NETWORK_SYMBOLS
from tg_nft_bot.utils.credentials import URL
from tg_nft_bot.streams.streams_operations import (
    create_stream,
    delete_stream,
)
from tg_nft_bot.nft.nft_operations import get_collection_info
from tg_nft_bot.nft.nft_constants import OPENSEA_NETWORK

from tg_nft_bot.bot.bot_utils import application, webhook_update

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


#################################################################
#######################     BOT      ############################
#################################################################

# standard messages
cancel_message = "Use /start in group chat to restart the bot."
title_message = "*CONFIG MENU*\n\n"


# states
MAIN, NETWORK, CONTRACT, MINTER, WEBSITE, ADD_CONFIG = range(6)
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
            InlineKeyboardButton("TRON", callback_data="tron-mainnet"),
            InlineKeyboardButton("ARB", callback_data="arbitrum-mainnet"),
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
                delete_stream(collection["webhookId"])
                delete_config_by_id(collection["id"])
            else:
                for chat in collection["chats"]:
                    if chat != update.effective_chat.id:
                        new_chats.append(chat)

                update_chats_by_id(collection["id"], new_chats)


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

            [name, slug] = get_collection_info(context.network, context.contract)

            if name == None:
                raise Exception("Invalid contract address.")

            if website[:8] != "https://":
                if context.network == "tron-mainnet":
                    website = "https://apenft.io/#/collection/" + context.contract
                else:
                    website = (
                        "https://opensea.io/assets/"
                        + OPENSEA_NETWORK[context.network]
                        + "/"
                        + context.contract
                    )

            route = "/" + slug
            create_webhook_route(route)

            webhook_id = create_stream(
                network=context.network, contract=context.contract, route=route
            )

            entry = check_if_exists(context.network, context.contract)
            if entry is None:
                # TODO:
                # check if contract exists

                add_config(
                    name,
                    slug,
                    context.network,
                    context.contract,
                    context.minter,
                    website,
                    webhook_id,
                    [context.chat],
                )
                status = "_Collection is added._"
            else:

                chats: list[str] = query_chats_by_contract(context.network, context.contract)

                exist_count = chats.count(context.chat)
                if exist_count == 0:
                    chats.append(context.chat)

                update_config(
                    name,
                    slug,
                    context.network,
                    context.contract,
                    context.minter,
                    website,
                    webhook_id,
                    chats,
                )

                status = "_Collection is updated._"
        except Exception as e:
            traceback.print_exc()
            status = (
                "_Configuration failed: "
                + str(e)
                + "\nPlease start over and try again._"
            )

        message_text = title_message
        message_text += (
            "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
        )
        message_text += "Contract Address: *" + context.contract + "*\n\n"
        message_text += "Minter Address: *" + context.minter + "*\n\n"
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

async def enter_minter(update: Update, context: CustomContext):

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

            return CONTRACT

    # process text entry
    else:

        minter = "0x0000000000000000000000000000000000000000" if update.message.text == "0" else update.message.text

        user_message = update.message
        await user_message.delete()

        
        if minter is not None and is_address(minter):
            context.minter =  Web3.to_checksum_address(minter)
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "Contract Address: *" + context.contract + "*\n\n"
            message_text += "Minter Address: *" + minter + "*\n\n"
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
            message_text += "Contract Address: *" + context.contract + "*\n\n"
            message_text += "Minter Address: *" + minter + "*\n\n"
            message_text += "_Please enter a valid minter address or enter '0' for regular mints:_\n\n"
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.menu,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
            )
            return CONTRACT

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

        if contract is not None and is_address(contract):
            context.contract = contract
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "Contract Address: *" + contract + "*\n\n"
            message_text += "_Enter '0' if regular minting contract or specify minter address':_\n\n"
            reply_markup = return_menu()

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                text=message_text,
                message_id=context.menu,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,
            )

            return MINTER

        else:
            message_text = title_message
            message_text += (
                "Selected Network: *" + NETWORK_SYMBOLS[context.network] + "*\n\n"
            )
            message_text += "Contract Address: *" + contract + "*\n\n"
            message_text += "_Please enter a valid contract address:_\n\n"
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
                        try:
                            admins = await application.bot.get_chat_administrators(chat)
                            admin_ids = [admin["user"]["id"] for admin in admins]
                            if update.effective_user.id in admin_ids:
                                chats_isAdmin.append(chat)
                        except Exception:
                            pass

                    # throw exception if user is not admin in any of the configured groups
                    if len(chats_isAdmin) > 0:
                        if(network == "tron-mainnet"):
                            contract = Tron.to_base58check_address(Tron.to_hex_address(contract))
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

                if len(config_buttons) == 0:
                    raise Exception("No configurations found.")
                
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
                collection["minter"],
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
            delete_stream(collection["webhookId"])
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

            # configure website
            if len(r["website"]) > 8:
                website = r["website"]
            elif network == "tron-mainnet":
                website = "https://apenft.io/#/collection/" + contract
            else:
                website = (
                    "https://opensea.io/assets/"
                    + OPENSEA_NETWORK[network]
                    + "/"
                    + contract
                )

            # output message
            message_text += f"<u><b>CONFIG {index}:</b></u>\nName: {name}\nNetwork: {NETWORK_SYMBOLS[network]}\nCA: {contract}\nWebsite: {website}\nChats: "

            # send message to bot
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
            MINTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_minter),
                CallbackQueryHandler(enter_minter),
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
