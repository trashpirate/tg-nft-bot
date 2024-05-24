import asyncio
from http import HTTPStatus
from flask import Flask, Response, abort, make_response, request
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from web3 import Web3

from bot import parse_tx, start_app, update_queue
from models import CollectionConfigs, db
from credentials import DATABASE_URL, PORT

# Set up webserver
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


async def main() -> None:

    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()

        config = CollectionConfigs(
            name="Flames",
            network="ETH_MAINNET",
            address=Web3.to_checksum_address(
                "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775"
            ),
            website="https://flames.buyholdearn.com",
            webhookid="wh_b8u3wiwfvlgaoo5w",
            chats=[-1002172847802],
        )
        db.session.add(config)

        config = CollectionConfigs(
            name="Flamelings",
            network="ETH_MAINNET",
            address=Web3.to_checksum_address(
                "0x49902747796C2ABcc5ea640648551DDbc2c50ba2"
            ),
            website="https://flamelings.buyholdearn.com",
            webhookid="wh_5h037g75hod37wli",
            chats=[-1002172847802],
        )
        db.session.add(config)

        config = CollectionConfigs(
            name="Liquid",
            network="BASE_MAINNET",
            address=Web3.to_checksum_address(
                "0x0528C4DFc247eA8b678D0CA325427C4ca639DEC2"
            ),
            website="https://liquid.buyholdearn.com",
            webhookid="wh_sew45jozete6t584",
            chats=[-1002172847802],
        )
        db.session.add(config)
        db.session.commit()

    @app.post("/telegram")
    async def telegram() -> Response:
        # Handle incoming Telegram updates by putting them into the `update_queue`
        await update_queue(request.json)
        return Response(status=HTTPStatus.OK)

    @app.route("/nfts", methods=["GET", "POST"])
    async def nft_udpates() -> Response:
        # Handle incoming NFT updates by putting them into the `update_queue`

        try:
            json_data = request.json
            await parse_tx(json_data)
            return Response(status=HTTPStatus.OK)

        except KeyError:
            abort(
                HTTPStatus.BAD_REQUEST,
                "Please pass all query parameters.",
            )
        except ValueError:
            abort(HTTPStatus.BAD_REQUEST, "No valid data.")

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(app),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    bot = await start_app()
    # Run bot and webserver together
    async with bot:
        await bot.start()
        await webserver.serve()
        await bot.stop()


if __name__ == "__main__":
    # main()
    asyncio.run(main())
