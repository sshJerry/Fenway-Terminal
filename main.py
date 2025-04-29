
from dotenv import load_dotenv
import schwabdev
import logging
import os
import schwabdev
from config.config import SCHWAB_URL, SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL, SCHWAB_TOKEN_URL, \
    SCHWAB_TEMPLATE_URL, SCHWAB_BASE_URL

import json
from collections import defaultdict

def main():
    ##auth.main()
    load_dotenv()
    if len(SCHWAB_APP_KEY) != 32 or len(SCHWAB_SECRET) != 16:
        raise Exception("Add you app key and app secret to the .env file.")

    logging.basicConfig(level=logging.INFO)
    client = schwabdev.Client(SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL)
    streamer = client.stream

    def my_handler(message):
        #print("test_handler:" + message)
        data = json.loads(message)
        print(data)
    streamer.start(my_handler)
    #streamer.send(streamer.level_one_equities("TSLA, CRWD, PLTR", "0,1,2,3"))
    streamer.send(streamer.level_one_futures("/ES", "0,1,2,3"))


    import time
    time.sleep(60)
    streamer.stop()

if __name__ == "__main__":
    main()


