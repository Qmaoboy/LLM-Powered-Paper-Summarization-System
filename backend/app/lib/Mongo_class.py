from pymongo import MongoClient
import pymongo
from gridfs import GridFS
from bson import ObjectId
from PIL import Image
from io import BytesIO

class mongo_client():
    def __init__(self,database_name="Innolux",collection_name="Paper",domain='localhost',port=27023) -> None:
        self.client = MongoClient(domain, port)
        self.db_name=database_name
        self.db=self.client[self.db_name]
        self.collection=self.db[collection_name]
        self.key="Paper_name"
        self.collection.create_index([(self.key, pymongo.ASCENDING)], unique=True)
        self.fs = GridFS(self.db, collection='Image_Figure')  # 替换为实际的GridFS集合名称
    def Mongo_insert_text(self,pubname,data_list):
        ## Data_list is a list of dictionary
        ## makesure in data dict key is "Patent_name" when insert
        update_data = {'$set': data_list}
        filter_criteria = {'Paper_name': pubname}  # 替换为实际的查询条件
        result=self.collection.update_one(filter_criteria, update_data,upsert=True)
        # result_many = self.collection.insert_many(data_list)
        if result.matched_count!=0:
            print(f'Modify DB {self.db_name} Paper Name: {pubname} => {data_list["title_name"]}' )
        else:
            print(f'Add DB {self.db_name} Paper Name: {pubname} ')
        # return result

    def Mongo_get_image_id(self,image_path,File_path=True):
        ## image_path is the absolute path of image
        ## File_name as the search key Pattern is "Paper_name_Image_index"
        ## makesure in data dict key is "Patent_name" when insert
        if File_path:
            with open(image_path, 'rb') as file:
                file_id = self.fs.put(image_path, contentType='image/png')
        else:
            file_id = self.fs.put(image_path, contentType='image/png')
        return file_id

    def Mongo_find(self,query):
        ## query_list is a list of dictionary
        ## make sure query_list contain "Paper_name" as key
        return self.collection.find_one({self.key:query})
        # result=[]
        # for i in query:
        #     result_documents = self.collection.find(i)
        #     for document in result_documents:
        #         result.append(document)
        # return result

    def Mongo_drop_collection(self,collection_name):
        print(f"Drop collection {collection_name}")
        self.db.drop_collection(collection_name)

    def Mongo_drop_database(self,database_name):
        print(f"Drop database {database_name}")
        self.client.drop_database(database_name)

    def Mongo_Close(self):
        self.client.close()

    def Mongo_update(self,old,new):
        Old_data={'Paper_name':old}
        Update_data={'$set':new}
        self.client.update_one(Old_data,Update_data)

    def Mongo_Read_ImageID(self,Image_ID):
        retrieved_file = self.fs.get(ObjectId(Image_ID))
        image_data = retrieved_file.read()
        image = Image.open(BytesIO(image_data))
        return image

    def Mongo_Read_ImageID_File(self,Image_ID):
        retrieved_file = self.fs.get(ObjectId(Image_ID))
        image_data = retrieved_file.read()
        # img_bytesio = BytesIO(image_data)
        image = Image.open(BytesIO(image_data))
        img_bytesio = BytesIO()
        image.save(img_bytesio, format='PNG')
        return img_bytesio
