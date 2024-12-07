from linebot.v3.liff import(
    ApiClient,
    Configuration,
    Liff
)
from linebot.v3.liff.models.get_all_liff_apps_response import GetAllLiffAppsResponse
from linebot.v3.liff.rest import ApiException
import os
from pprint import pprint

import linebot.v3.oauth
from linebot.v3.oauth.models.issue_stateless_channel_access_token_response import IssueStatelessChannelAccessTokenResponse
class LiffService:
    def __init__(self, liff_id):
        self.liff_id = liff_id
        self.configuration = Configuration(access_token="dkKrsEyxd3HGUgDxaF5yeWvj2rs8Y1q9erWTOLuYJ0UxVTSYki2cqd25c6N711mF681tn8A00/YJjwgnlKdC7y5Eq5xx/mcU5+1gd7jE+1eamKIefsrUDQ3AgQfs4EC2EbOkKI4eA3/rALl/toUnm49PbdgDzCFqoOLOYbqAITQ=")

    def issue_stateless_channel_access_token(self):
        configuration = linebot.v3.oauth.Configuration(
            host = "https://api.line.me"
        )
        with linebot.v3.oauth.ApiClient(configuration) as api_client:
            # Create an instance of the API class
            api_instance = linebot.v3.oauth.ChannelAccessToken(api_client)
            grant_type = 'client_credentials' # str | `client_credentials`
            client_id = '2005359561' # str | Channel ID.
            client_secret = 'd09c19fa15ceaacf1858abf00516b307' # str | Channel secret.

            try:
                api_response = api_instance.issue_stateless_channel_token_with_http_info(grant_type=grant_type, client_id=client_id, client_secret=client_secret)
                print("The response of ChannelAccessToken->issue_stateless_channel_token:\n")
                pprint(api_response)
            except Exception as e:
                print("Exception when calling ChannelAccessToken->issue_stateless_channel_token: %s\n" % e)
    def get_all_liff_apps(self):
        with ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            liff_api = Liff(api_client)

            try:
                # Get all LIFF apps
                api_response = liff_api.get_all_liff_apps()
                print("The response of Liff->get_all_liff_apps:\n")
                pprint(api_response)
            except Exception as e:
                print("Exception when calling Liff->get_all_liff_apps: %s\n" % e)