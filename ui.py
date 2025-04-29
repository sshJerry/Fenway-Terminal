import time
import os
import threading
import logging
from data_manager import DataManager # Import the DataManager class

class TerminalUI(threading.Thread):
    def __init__(self, data_manager: DataManager, symbols_to_display: list, refresh_rate_seconds=0.5):
        """
        Initializes the Terminal UI thread.

        Args:
            data_manager: An instance of DataManager to get data from.
            symbols_to_display: A list of symbols (strings) to show in the UI.
            refresh_rate_seconds: How often to redraw the terminal (in seconds).
        """
        super().__init__()
        self.data_manager = data_manager
        self.symbols = symbols_to_display
        self.refresh_rate = refresh_rate_seconds
        # Use an Event to signal the thread to stop gracefully
        self._stop_event = threading.Event()
        self._logger = logging.getLogger(__name__)

    def run(self):
        """
        The main loop for the UI thread. Continuously updates the display.
        """
        self._logger.info("Terminal UI thread started.")
        try:
            while not self._stop_event.is_set():
                self.display_data()
                # Wait for the refresh rate or until the stop event is set
                self._stop_event.wait(self.refresh_rate)
        except Exception as e:
            self._logger.error(f"Error in Terminal UI thread: {e}", exc_info=True)
        finally:
            self._logger.info("Terminal UI thread stopped.")


    def display_data(self):
        """
        Clears the terminal and prints the current market data for the symbols.
        """
        # Clear the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

        print("--- Real-time Market Data ---")
        print("-" * 60) # Adjust width as needed

        # Get the field names from the DataManager
        field_names = self.data_manager.get_field_names()

        # Define which fields to display and their order + formatting
        display_fields_config = {
            'Symbol': {'header': 'Symbol', 'width': 10, 'align': '<'},
            'Bid Price': {'header': 'Bid', 'width': 12, 'align': '>'},
            'Ask Price': {'header': 'Ask', 'width': 12, 'align': '>'},
            'Last Price': {'header': 'Last', 'width': 12, 'align': '>'},
            # Add other fields you want to display here
            # 'Volume': {'header': 'Volume', 'width': 10, 'align': '>'},
        }

        # Map field_map names to display_fields_config keys for easy lookup
        # This is necessary because self.data_manager._market_data uses field_map names
        display_keys_from_field_map = {field_names[id]: key for key, config in display_fields_config.items() for id, name in field_names.items() if name == key}


        # Build header string
        header_parts = []
        separator_parts = []
        for field_key, config in display_fields_config.items():
             header_parts.append(f"{config['header']:{config['align']}{config['width']}}")
             separator_parts.append("-" * config['width'])

        print("".join(header_parts))
        print("".join(separator_parts))

        # Display data for each symbol
        for symbol in self.symbols:
            data = self.data_manager.get_data(symbol) # Get data from DataManager
            line_parts = []
            if data:
                 for field_key, config in display_fields_config.items():
                     # Get the actual key used in the data_manager's dictionary
                     data_key = display_keys_from_field_map.get(field_key, field_key) # Fallback to key itself if not mapped

                     # Get the value, default to 'N/A' if not present yet
                     value = data.get(data_key, 'N/A')

                     # Format the value
                     # You might want more specific formatting for numbers, e.g., f"{value:.2f}"
                     formatted_value = str(value)

                     line_parts.append(f"{formatted_value:{config['align']}{config['width']}}")
                 print("".join(line_parts))
            else:
                 # Display waiting message if no data is available yet for the symbol
                 print(f"{symbol:{display_fields_config['Symbol']['align']}{display_fields_config['Symbol']['width']}}"
                       f"{'Waiting for data...':<{sum(c['width'] for k, c in display_fields_config.items() if k != 'Symbol')}}")


        print("-" * 60)
        print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("(Press Ctrl+C to stop)")


    def stop(self):
        """
        Signals the UI thread to stop its loop.
        """
        self._stop_event.set()