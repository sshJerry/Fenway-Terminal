import base64
import webbrowser

import requests
from loguru import logger

from config.config import SCHWAB_URL, SCHWAB_APP_KEY, SCHWAB_SECRET, SCHWAB_CALLBACK_URL, SCHWAB_TOKEN_URL, \
    SCHWAB_TEMPLATE_URL, SCHWAB_BASE_URL

"""
Access token expires after 30 minutes.
To maintain access token, we'll be exchanging current refresh token with Schwab and retrieving a new access
token (while the refresh token stays constant) every 29 minutes to ensure you have a working access token at all times

Initial authentication needs to be done every 7 days because Schwab forces the refresh token expiration after 7 days. 
"""
def init_auth_url() -> tuple[str, str, str]:
    logger.info("Initializing OAuth Authentication URL")
    logger.info("Connecting to Schwab OAuth... {}", SCHWAB_TEMPLATE_URL)
    logger.debug("Constructed IRL: {}", SCHWAB_URL)

def construct_headers_and_payload(returned_url):
     response_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

     credentials = f"{SCHWAB_APP_KEY}:{SCHWAB_SECRET}"
     base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
          "utf-8"
     )

     headers = {
          "Authorization": f"Basic {base64_credentials}",
          "Content-Type": "application/x-www-form-urlencoded",
     }

     payload = {
          "grant_type": "authorization_code",
          "code": response_code,
          "redirect_uri": SCHWAB_CALLBACK_URL,
     }

     return headers, payload

def retrieve_tokens(headers, payload) -> dict:
    init_token_response = requests.post(
        url=SCHWAB_TOKEN_URL,
        headers=headers,
        data=payload,
    )

    init_tokens_dict = init_token_response.json()

    return init_tokens_dict

def main():
     init_auth_url()

     logger.info("Opening Web Browser...")
     webbrowser.open(SCHWAB_URL)

     logger.info("After signing in, paste the url below...")
     returned_url = input()
     logger.debug("Input URL: {}", returned_url)

     logger.info("Constructing Headers and Payload in preparation for token request...")
     init_token_headers, init_token_payload = construct_headers_and_payload(returned_url)
     logger.info("Requesting Tokens...")
     init_tokens_dict = retrieve_tokens(headers=init_token_headers, payload=init_token_payload)

     logger.debug(init_tokens_dict)

     logger.info("You've been authenticated")

     access_token = init_tokens_dict["access_token"]
     refresh_token = init_tokens_dict["refresh_token"]
     base_url = SCHWAB_BASE_URL
     response = requests.get(f'{base_url}/quotes', headers={"Authorization": f'Bearer {access_token}'},
                             params={"symbols":"MVIS,NVDA,AMD",
                                     "fields": "quote",
                                     "indicative" : "false"},
                             timeout=1000)
     response_inspection = response.json()
     logger.info(response_inspection)
     return "Done!"

if __name__ == "__main__":
    main()