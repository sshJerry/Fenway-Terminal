from dotenv import load_dotenv
import schwabdev
import logging
import os
import time
import sys
import threading # Needed if streamer doesn't keep main alive, or for clean exit

# Import configuration
# from config.config import SCHWAB_URL, SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL, SCHWAB_TOKEN_URL, \
#     SCHWAB_TEMPLATE_URL, SCHWAB_BASE_URL # Import what you actually need
from config.config import SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL

# Import custom modules
from data_manager import DataManager
from ui import TerminalUI

def main():
    # --- Setup ---
    load_dotenv()

    # Basic configuration validation
    if len(SCHWAB_APP_KEY) != 32 or len(SCHWAB_SECRET) != 16:
        raise Exception("Add your app key (32 chars) and app secret (16 chars) to the .env file.")

    # Set up logging
    logging.basicConfig(level=logging.INFO, # Use INFO for production, DEBUG for development
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logging.getLogger("schwabdev").setLevel(logging.INFO) # Adjust library logging level if noisy

    # --- Initialization ---
    logger.info("Initializing Schwab client...")
    # Assuming schwabdev handles authentication flow here or requires prior auth
    client = schwabdev.Client(SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL)
    streamer = client.stream # Get the streamer instance
    logger.info("Schwab client initialized.")

    # --- Data Management ---
    # Create an instance of our DataManager
    data_manager = DataManager()
    logger.info("DataManager created.")

    # --- Set up the Streamer Handler ---
    # The streamer will call this function whenever a new message arrives.
    # This function simply passes the message to our DataManager.
    def streamer_callback(message):
        data_manager.handle_message(message)

    # Start the streamer and register our callback
    logger.info("Starting Schwab streamer...")
    # The streamer.start() method likely runs in a separate thread or manages an event loop internally.
    streamer.start(streamer_callback)
    logger.info("Schwab streamer started.")


    # --- Subscribe to Data ---
    # Define the symbols and fields you want to subscribe to
    futures_symbols = ["/ES", "/NQ", "/CL"] # Example futures symbols
    equity_symbols = ["AAPL", "GOOG", "MSFT", "TSLA", "PLTR"] # Example equity symbols
    # Fields to subscribe to (Symbol, Bid, Ask, Last) - Ensure DataManager.field_map includes these IDs
    fields_to_subscribe = "0,1,2,3" # You can add more fields like 4,5,8,9,10,11 etc.

    all_symbols_to_subscribe = futures_symbols + equity_symbols

    # Subscribe to futures
    logger.info(f"Subscribing to futures: {futures_symbols} with fields {fields_to_subscribe}")
    for symbol in futures_symbols:
         try:
             streamer.send(streamer.level_one_futures(symbol, fields_to_subscribe))
             # Add a small delay between subscriptions to avoid hitting rate limits
             time.sleep(0.1)
         except Exception as e:
              logger.error(f"Failed to subscribe to future {symbol}: {e}")


    # Subscribe to equities (Assuming schwabdev has a similar method)
    # You might need to adjust the method name (e.g., level_one_equities)
    # and verify if the field IDs (0,1,2,3) are the same for equities.
    logger.info(f"Subscribing to equities: {equity_symbols} with fields {fields_to_subscribe}")
    for symbol in equity_symbols:
         try:
            # Check schwabdev documentation for the correct equity subscription method
            # Example (might need adjustment):
            streamer.send(streamer.level_one_equities(symbol, fields_to_subscribe))
            logger.warning(f"Equity subscription for {symbol} is commented out. Implement according to schwabdev docs.")
            time.sleep(0.1)
         except Exception as e:
              logger.error(f"Failed to subscribe to equity {symbol}: {e}")


    # --- UI Component ---
    # Create an instance of our TerminalUI, giving it access to the DataManager
    # Pass the list of symbols we want the UI to display
    ui = TerminalUI(data_manager, all_symbols_to_subscribe, refresh_rate_seconds=0.2) # Refresh every 0.2 seconds
    logger.info("TerminalUI created.")

    # Start the UI thread
    ui.start()
    logger.info("TerminalUI thread started.")


    # --- Keep Main Thread Alive ---
    # The schwabdev streamer likely runs in its own thread(s).
    # Our UI also runs in a separate thread.
    # The main thread needs to stay alive to keep the program running.
    # We can wait for a KeyboardInterrupt (Ctrl+C) to signal shutdown.
    try:
        # Keep the main thread active. This prevents the program from exiting
        # as long as other non-daemon threads (like our UI thread or streamer threads) are running.
        # Using a simple infinite loop with sleep is one way.
        while True:
            time.sleep(1) # Sleep to avoid busy-waiting

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Initiating shutdown...")

    finally:
        # --- Clean Shutdown ---
        logger.info("Stopping UI thread...")
        ui.stop()       # Signal the UI thread to stop
        ui.join()       # Wait for the UI thread to finish

        logger.info("Stopping Schwab streamer...")
        streamer.stop() # Signal the streamer to stop
        # Depending on schwabdev implementation, you might need to join streamer threads too
        # if streamer.start() returns a thread object or provides a join method.
        # If streamer.stop() is blocking or closes the underlying connection, this might be enough.

        logger.info("Application shutdown complete.")
        sys.exit(0) # Exit cleanly

if __name__ == "__main__":
    main()