import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import threading

class FireBaseService:
    def __init__(self, cred):
        self.cred = credentials.Certificate(cred)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        self.callback_done = threading.Event()

    def get_collection_data(self, collection):
        """取得集合所有資料"""
        docs = self.db.collection(collection).stream()
        return [doc.to_dict() for doc in docs]

    def get_data(self, collection, doc_id):
        """取得資料"""
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        return doc.to_dict()
    
    def filter_data(self, collection, conditions, order_by=None):
        """篩選資料"""
        collection_ref = self.db.collection(collection)
        for condition in conditions:
            collection_ref = collection_ref.where(filter=FieldFilter(*condition))
        if order_by:
            collection_ref = collection_ref.order_by(order_by)
        docs = collection_ref.stream()
        return [doc.to_dict() for doc in docs]
    
    
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

    def on_snapshot(self, collection):
        """監聽文件變更"""
        def callback(doc_snapshot, changes, read_time):
            for change in changes:
                # 檢測變更類型
                if change.type.name == 'MODIFIED':
                    print(f"Document modified: {change.document.id}")
                    self.update_correct_rate(change.document)

        # 監聽集合
        doc_ref = self.db.collection(collection)
        doc_watch = doc_ref.on_snapshot(callback)
        return doc_watch

    def update_correct_rate(self, document):
        """根據 total_count 和 correct_count 更新 correct_rate"""
        data = document.to_dict()
        total_count = data.get('total_count', 0)
        correct_count = data.get('correct_count', 0)

        # 避免除以零的錯誤
        correct_rate = round((correct_count / total_count)*100, 2) if total_count > 0 else 0

        # 更新文檔的 correct_rate 欄位
        document.reference.update({
            'correct_rate': correct_rate
        })
        print(f"Updated correct_rate for document {document.id}: {correct_rate}")
