import asyncio
from http import HTTPStatus
from flask import Flask, Response, abort, make_response, request
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from web3 import Web3

from bot import parse_tx, start_app, update_queue
from models import CollectionConfigs, db, initial_config
from credentials import DATABASE_URL, PORT, GROUP_IDS

from app import flask_app


async def main() -> None:

    await initial_config()

    @flask_app.post("/telegram")
    async def telegram() -> Response:
        # Handle incoming Telegram updates by putting them into the `update_queue`
        json_data = request.json
        await update_queue(json_data)
        return Response(status=HTTPStatus.OK)

    @flask_app.route("/nfts", methods=["POST"])
    async def nft_udpates() -> Response:
        # Handle incoming NFT updates by putting them into the `update_queue`

        try:
            json_data = request.json
            await parse_tx(json_data)
            return Response(status=HTTPStatus.OK)

        except:
            print("Invalid request.")
            return Response(status=HTTPStatus.OK)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    print("Initialize bot...")
    bot = await start_app()

    print("Run bot and webserver together...")
    async with bot:
        await bot.start()
        print("Bot started. Starting Server...")
        await webserver.serve()
        await bot.stop()


if __name__ == "__main__":
    # main()
    asyncio.run(main())
