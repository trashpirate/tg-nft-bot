import asyncio
from http import HTTPStatus
from flask import Response, request
import uvicorn
from asgiref.wsgi import WsgiToAsgi

from bot import start_app, update_queue, update_webhook_queue, create_webhook_route

from models import initial_config, query_table
from credentials import PORT, TEST

from app import flask_app


async def main() -> None:

    initial_config()

    # get all the configured chats and create the webhook routes on restart
    collection_list = query_table()
    print(collection_list)
    if len(collection_list) > 0:
        for collection in collection_list:
            create_webhook_route("/" + collection["slug"])
            print("route: " + collection["slug"])

    @flask_app.post("/telegram")
    async def telegram() -> Response:
        # Handle incoming Telegram updates by putting them into the `update_queue`
        json_data = request.json
        await update_queue(json_data)
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
        print("Test mode: " + TEST)
        await webserver.serve()
        await bot.stop()


if __name__ == "__main__":
    # main()
    asyncio.run(main())
