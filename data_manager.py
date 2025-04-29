import threading
import json
import logging
from collections import defaultdict

class DataManager:
    def __init__(self):
        # Use a dictionary to store the latest state for each symbol
        # {symbol: {field_name: value, ...}}
        self._market_data = {}
        # Use a lock because the streaming handler runs in a separate thread
        # and the UI thread will read from this dictionary.
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)

        # Mapping of Schwab field IDs to readable names
        # Extend this as you subscribe to more fields
        self.field_map = {
            '0': 'Symbol',
            '1': 'Bid Price',
            '2': 'Ask Price',
            '3': 'Last Price',
            # Add other fields you subscribe to, e.g.,
            # '4': 'Bid Size',
            # '5': 'Ask Size',
            # '8': 'Volume',
            # '9': 'Open Price',
            # '10': 'High Price',
            # '11': 'Low Price',
            # ... refer to Schwab API documentation for full list
        }

    def handle_message(self, message_str):
        """
        Processes incoming streaming messages and updates the internal data state.
        This method is intended to be the callback for the Schwab streamer.
        """
        try:
            message = json.loads(message_str)
            self._logger.debug(f"Received message: {message}")

            # Check for data messages
            if 'data' in message:
                for item in message['data']:
                    # Only process 'SUBS' command for now
                    if item.get('command') == 'SUBS' and 'content' in item:
                        for content_item in item['content']:
                            self._process_content_item(content_item)

            # Handle heartbeat or other message types if needed
            elif 'notify' in message and 'heartbeat' in message['notify'][0]:
                 self._logger.debug(f"Heartbeat received: {message['notify'][0]['heartbeat']}")
            # Add checks for other message types (auth, login, etc.) if necessary
            # based on Schwab API documentation and schwabdev library behavior
            else:
                 self._logger.warning(f"Unhandled message type: {message}")


        except json.JSONDecodeError:
            self._logger.error(f"Failed to decode JSON message: {message_str}")
        except Exception as e:
            self._logger.error(f"Error processing message: {e}", exc_info=True)


    def _process_content_item(self, content_item):
        """
        Updates the internal data state for a single symbol based on the content item.
        Handles partial updates.
        """
        # 'key' is typically the symbol
        symbol = content_item.get('key')
        if not symbol:
            self._logger.warning(f"Received content item without a 'key' (symbol): {content_item}")
            return

        self._logger.debug(f"Processing update for symbol: {symbol}")

        # Acquire the lock before modifying the shared dictionary
        with self._lock:
            # If the symbol isn't in our data yet, initialize it.
            # Store the symbol itself under the 'Symbol' key using the mapping.
            if symbol not in self._market_data:
                 self._market_data[symbol] = {self.field_map.get('0', 'Symbol'): symbol}

            # Update the fields provided in the message
            for field_id, value in content_item.items():
                 # Only update if the field is in our map (i.e., it's a data field)
                 if field_id in self.field_map:
                      field_name = self.field_map[field_id]
                      self._market_data[symbol][field_name] = value
                      self._logger.debug(f"Updated {symbol} -> {field_name}: {value}")
                 # Optionally log unexpected fields
                 # elif field_id not in ['key', 'delayed', 'assetMainType']:
                 #      self._logger.debug(f"Ignoring unknown field ID '{field_id}' for symbol '{symbol}'")


    def get_data(self, symbol=None):
        """
        Retrieves the current data for a specific symbol or all symbols.
        Thread-safe.
        """
        with self._lock:
            if symbol:
                # Return data for a specific symbol, or None if not found
                return self._market_data.get(symbol, None)
            else:
                # Return a copy of the entire data dictionary to prevent
                # external code from modifying the internal state directly.
                return self._market_data.copy()

    def get_field_names(self):
        """Returns the mapping of field IDs to names."""
        return self.field_map.copy()