import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class FireBaseService:
    def __init__(self, cred):
        self.cred = credentials.Certificate(cred)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

    def get_collection_data(self, collection):
        """取得集合所有資料"""
        docs = self.db.collection(collection).stream()
        return [doc.to_dict() for doc in docs]

    def get_data(self, collection, doc_id):
        """取得資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        return doc.to_dict()
    
    def add_data(self, collection, doc_id, data):
        """新增資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.set(data)

    def update_data(self, collection, doc_id, data):
        """更新資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.update(data)

    def delete_data(self, collection, doc_id):
        """刪除資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc_ref.delete()

