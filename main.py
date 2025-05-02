import asyncio
from app.agent.manus import Manus
from app.logger import logger


async def main():
    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        prompt = input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":

    # argparser = argparse.ArgumentParser()
    # argparser.add_argument("--server", action="store_true", help="Run the server",dest="server")
    # argparser.add_argument("-p","--prompt", required=False, help="Executes the prompt directly",dest="prompt")

    # args = argparser.parse_args()

    # if not args.server:
        asyncio.run(main())

    # else:
    #     # asgi_app = WsgiToAsgi(app)
    #     asyncio.run(start_server())


