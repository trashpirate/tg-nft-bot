from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, List, Optional
import traceback

from flask import Response, request
from werkzeug.routing import Rule
from telegram import (
    LinkPreviewOptions,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CallbackContext,
    ExtBot,
    Application,
)
from web3 import Web3
from tg_nft_bot.db.db_operations import (
    query_collection,
    query_collection_by_webhook,
    query_minter_by_webhook,
)

# helpers
from tg_nft_bot.utils.networks import SCANS
from tg_nft_bot.utils.credentials import TOKEN

from tg_nft_bot.nft.nft_operations import (
    get_log_data,
    get_metadata,
    get_total_supply,
    get_url,
)
from tg_nft_bot.nft.nft_constants import MAGIC_EDEN, OPENSEA, RARIBLE

# app
from tg_nft_bot.bot.bot_config import flask_app


# context
class ChatData:
    """Custom class for chat_data. Here we store data per message."""

    def __init__(self) -> None:
        self.webhook: str = None
        self.name: str = None
        self.network: str = None
        self.contract: str = None
        self.minter: str = None
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
    def minter(self) -> Optional[str]:
        return self.chat_data.minter

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
    
    @minter.setter
    def minter(self, value: str) -> None:
        self.chat_data.minter = value

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
    webhook_id: str
    contract: str
    token_id: object
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
        receipts = json_data["receipts"]
    except Exception:
        try:
            try:
                receipts = json_data["data"]["receipts"]
            except Exception:
                try:
                    receipts = json_data["data"][0]["receipts"]
                except Exception:
                    raise Exception("No receipts found.")

        except Exception:
            traceback.print_exc()
            return None

    if len(receipts) < 1:
        # print("No new data.")
        return None

    # webhook id
    try:
        network = json_data["metadata"]["network"]
        webhook_id = json_data["metadata"]["stream_id"]
        logs_list = [log for receipt in receipts for log in receipt["logs"]]
        minter = query_minter_by_webhook(webhook_id)
        logs = get_log_data(network, minter, webhook_id, logs_list)
        return logs

    except Exception:
        traceback.print_exc()
        return None


async def webhook_update(
    update: WebhookUpdate, context: ContextTypes.DEFAULT_TYPE
) -> None:
    data_list = parse_tx(update.data)
    if data_list is None or len(data_list) == 0:
        return

    for data in data_list:
        collection = query_collection_by_webhook(data["webhook_id"])
        network = collection["network"]

        [img, text] = generate_output(
            network,
            data["contract"],
            data["owner"],
            data["token_id"],
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


def generate_output(network, contract, owner, token_id, hash, info):

    token_id = str(token_id)
    collection = query_collection(network, contract)

    minter = collection["minter"]
    collection_name = collection["name"]
    website = collection["website"]

    total_supply = get_total_supply(network, contract, minter)

    nft_data = get_metadata(network, contract, token_id)

    nft_name = nft_data["name"]
    nft_image = get_url(nft_data["image"], True)

    opensea = OPENSEA[network] + contract + "/" + token_id
    rarible = RARIBLE[network] + contract + ":" + token_id
    magicEden = MAGIC_EDEN[network] + contract + "/" + token_id
    apenft = "https://apenft.io/#/asset/" + contract + "/" + token_id

    scan = SCANS[network]

    if info["type"] == "mint":
        title = (f"NEW {collection_name} MINT!").upper()
        message = f"\n<b>{title}</b>\n"
    elif info["type"] == "sale":
        title = (f"NEW {collection_name} PURCHASE!").upper()
        message = f"\n<b>{title}</b>\n\n"

        price = info["price"]
        usd = info["price_usd"]
        currency = info["currency"]
        marketplace = info["marketplace"]
        message += f"Price: {price} {currency} ({usd} USD)\n"
        message += f"Marketplace: {marketplace.upper()}\n"

    message += f"\n<u><b>{nft_name}</b></u>\n"
    message += f"Token ID: {token_id}\n"

    message += '<a href="' + scan + "address/" + owner + '">Owner</a> | '
    message += '<a href="' + scan + "tx/" + hash + '">TX Hash</a> | '
    message += '<a href="' + scan + "token/" + contract + "#code" + '">Contract</a>\n'

    if nft_data["attributes"] is not None:
        message += "\n<u>Traits:</u>\n"
        for attr in nft_data["attributes"]:
            message += f'{attr["trait_type"]}: {attr["value"]}\n'

    if total_supply is not None:
        message += f"\nTotal minted: {total_supply}\n"

    message += '<a href="' + website + '">Website</a> | '

    if network == "tron-mainnet":
        message += '<a href="' + apenft + '">ApeNFT.io</a> '

    else:
        message += '<a href="' + opensea + '">Opensea</a> | '
        message += '<a href="' + rarible + '">Rarible</a> | '
        message += '<a href="' + magicEden + '">MagicEden</a>\n'

    message += "\n\nAD: "
    message += (
        '<a href="https://t.me/EARNServices">Book a slot to show your ad here!</a>\n'
    )
    message += "\n<i>Powered by @EARNServices</i>"

    return [nft_image, message]
