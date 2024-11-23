from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from config import Config
from api.firebase import FireBaseService

class Feature(ABC):
    config: Config = Config()
    firebaseService: FireBaseService = config.firebaseService

    @abstractmethod
    def execute_message(self, event, **kwargs):
        pass

    @abstractmethod
    def execute_postback(self, event, **kwargs):
        pass

class FeatureFactory:
    def __init__(self):
        self.feature_map: Dict[str, Type[Feature]] = {}

    def register(self, name: str, feature_class: Type[Feature]):
        self.feature_map[name] = feature_class

    def get_feature(self, feature_name: str) -> Optional[Feature]:
        feature_class = self.feature_map.get(feature_name)
        if feature_class:
            return feature_class()
        else:
            print(f"找不到對應的功能: {feature_name}")
            return None

feature_factory = FeatureFactory()

def register_feature(name: str):
    def decorator(cls):
        feature_factory.register(name, cls)
        return cls
    return decorator
