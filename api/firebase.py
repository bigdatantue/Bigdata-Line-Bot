import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class FireBaseService:
    def __init__(self, cred):
        self.cred = credentials.Certificate(cred)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        self.get_data('users', 'Lw0XBKyFmyfUhmxjNTeopUBPMAU2')

    def get_data(self, collection, doc_id):
        """取得資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            print(f"Document data: {doc.to_dict()}")
        else:
            print("No such document!")
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

