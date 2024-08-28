from linebot.v3.audience import (
    Configuration,
    ApiClient,
    ApiException,
    ManageAudience
)
from linebot.v3.audience.models import (
    CreateAudienceGroupRequest,
    CreateAudienceGroupResponse,
    AddAudienceToAudienceGroupRequest
)
import json
import os

class AudienceService:
    configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))

    @staticmethod
    def _create_audience_instance():
        with ApiClient(AudienceService.configuration) as api_client:
            return ManageAudience(api_client)

    @staticmethod
    def create_audience(description, user_ids: list):
        """
        建立受眾群組
        
        Args:
            description (str): 群組說明（名稱）
            user_ids (list): 使用者ID清單
        """
        audience_api = AudienceService._create_audience_instance()
        create_audience_group_request = CreateAudienceGroupRequest(
            description=description,
            audiences=[{'id': user_id} for user_id in user_ids]
        )
        
        #保留try-except，避免發生錯誤時程式中斷（若使用者帳號ID錯誤時會中斷執行）
        try:
            api_response = audience_api.create_audience_group_with_http_info(create_audience_group_request)
            audience_group = json.loads(api_response.raw_data)
            print(f"Audience Group ID: {audience_group.get('audienceGroupId')} Description: {audience_group.get('description')} created successfully.")
        except Exception as e:
            print(f"Exception when calling ManageAudience->create_audience_group: {e}")

    @staticmethod
    def add_audience_to_audience_group(audience_group_id: int, user_ids: list):
        """
        將使用者添加到受眾群組
        
        Args:
            audience_group_id (int): 受眾群組ID
            user_ids (list): 使用者ID清單
            
        Returns:
            dict: 操作成功會回傳None，否則回傳錯誤訊息
        """
        audience_api = AudienceService._create_audience_instance()
        add_audience_to_audience_group_request = AddAudienceToAudienceGroupRequest(
            audienceGroupId=audience_group_id,
            audiences=[{'id': user_id} for user_id in user_ids]
        )
        return audience_api.add_audience_to_audience_group(add_audience_to_audience_group_request)

    @staticmethod
    def delete_audience(audience_group_id: int):
        """
        刪除受眾群組
        
        Args:
            audience_group_id (int): 受眾群組ID
        
        Returns:
            dict: 操作成功會回傳None，否則回傳錯誤訊息
        """
        audience_api = AudienceService._create_audience_instance()
        
        #保留try-except，避免發生錯誤時程式中斷（若刪除成功的話會return None，而找不到該群組ID會中斷執行）
        try:
            api_response = audience_api.delete_audience_group(audience_group_id)
            if api_response is None:
                print(f"Audience Group ID:{audience_group_id} deleted successfully.")
            return api_response
        except Exception as e:
            print(f"Exception when calling ManageAudience->delete_audience_group: {e}")
        

    @staticmethod
    def get_audience_groups(page: int = 1):
        """
        獲取受眾群組列表
        
        Args:
            page (int): 頁碼
        
        Returns:
            dict: 包含受眾群組資訊或錯誤訊息
        """
        audience_api = AudienceService._create_audience_instance()
        return audience_api.get_audience_groups(page=page)