import pymysql
import json,yaml
import os
from dbutils.pooled_db import PooledDB
from lib.ppt_maker import *
import lib.logger as logger
import datetime
import threading as th
os.makedirs('log', exist_ok=True)
logger = logger.setup_logger(f'log/{datetime.datetime.now().strftime("%Y-%m-%d_%H")}_backend.log')

class mysql_db_client:
    def __init__(self,args) -> None:
        self.args=args
        self.create_database()
        self.db_pool()
        self.get_connection()
        # logger.info(f"{th.current_thread().name} Database Connection Success")

    def db_pool(self):
        thread_size = self.args['MainConfig']['thread_size']

        self.mysql_pool = PooledDB(
            creator=pymysql,  # Database library to use
            maxconnections=thread_size + 5,  # Maximum allowed number of connections in the pool
            mincached=1,  # Minimum number of idle connections in the pool at initialization
            maxcached=thread_size,  # Maximum number of idle connections in the pool
            maxshared=thread_size,  # Maximum number of shared connections in the pool
            blocking=True,  # Block if the pool reaches its maximum size until a connection is available
            maxusage=1000,  # Maximum number of times a single connection can be reused
            setsession=['SET wait_timeout = 31536000'],  # List of SQL commands to run when a connection is created
            ping=10,  # Checks connection health before using it (1 means check before every request)
            host=self.args['sql_config']['host'],
            port=int(self.args['sql_config']['port']),
            user=self.args['sql_config']['user'],
            password=self.args['sql_config']['password'],
            database=self.args['sql_config']['database_name'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def get_connection(self):
        try:
            self.connection = self.mysql_pool.connection()
            self.connection.ping(reconnect=True)
        except Exception as e:
            logger.debug(f"{th.current_thread().name} Error connecting to MySQL: {e}")
            os._exit(0)

    def create_database(self):
        connection = pymysql.connect(host=self.args['sql_config']['host'], user=self.args['sql_config']['user'], password=self.args['sql_config']['password'],port=self.args['sql_config']['port'],charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            check_database_query = f"CREATE DATABASE IF NOT EXISTS {self.args['sql_config']['database_name']}"
            cursor.execute(check_database_query)
            connection.commit()

    def Show_tables(self):
        with self.connection.cursor() as cursor:
            # 查询数据
            sql = "SHOW TABLES"
            cursor.execute(sql)
            result = cursor.fetchall()
            for row in result:
                logger.info(f"Get table name :{row}")
            return result

    def create_table(self,table_):
        if table_ in self.args['sql_config']['table_name']:
            columns=",".join([f"{k} {v}" for k,v in self.args[table_].items()])
            print(f"{table_}:\n{columns}")
            with self.connection.cursor() as cursor:
                # 创建表
                sql = f'''
                CREATE TABLE IF NOT EXISTS {table_} (
                    {columns}
                )
                '''
                cursor.execute(sql)
                self.connection.commit()

    def createcolumn(self,table_name,column_name,column_type):
        with self.connection.cursor() as cursor:
            # 创建欄位
            sql = f'''
            ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}
            '''
            cursor.execute(sql)
            self.connection.commit()

    def insert_data(self,table_name:str,condition_col,update_data:dict):
        # update_data= [dict1,dict2]
        # Fina Data
        results = self.find_data(table_name,condition_col,update_data[condition_col])
        if not results:
            # 插入数据
            update_data_column=[k for k,v in update_data.items() if k in self.args[table_name]]
            value_format=",".join(["%s"] *len(update_data_column))
            colunms=",".join(update_data_column)
            data_to_insert=[tuple(json.dumps(v) if self.args[table_name][k]=="json" else v for k,v in update_data.items())]
            try:
                with self.connection.cursor() as cursor:
                    sql = f"INSERT INTO {table_name} ({colunms}) VALUES ({value_format})"
                    cursor.executemany(sql,data_to_insert)
                    self.connection.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Insert Error: {e}")
                return None
        else:
            return self.update_data_by_condition(table_name,condition_col,update_data)

    def Fetch_back(self,table_name,results):
        output=[]
        if results:
            for idx,i in enumerate(results):
                res={}
                for key,value in i.items():
                    if value:
                        if "json"== self.args[table_name][key]:
                            res[key]=json.loads(value)
                        elif "INT" in self.args[table_name][key]:
                            res[key]=int(value)
                        else:
                            res[key]=value
                    else:
                        res[key]=None
                output.append(res)
            return output
        else:
            return output


    def check_exist_one(self,table_name,condision,check_val):
        with self.connection.cursor() as cursor:
            # 查询数据
            sql = f"SELECT * FROM {table_name} WHERE {condision}=%s"
            cursor.execute(sql,(check_val,))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False

    def find_data(self,table_name,target_col,target_val):
        with self.connection.cursor() as cursor:
            # 查询数据
            if self.args[table_name][target_col]=="json":
                sql = f"SELECT * FROM {table_name} WHERE JSON_CONTAINS({target_col}, %s)"
                cursor.execute(sql, (json.dumps(target_val),))
                results = cursor.fetchall()
                return self.Fetch_back(table_name,results)
            else:
                sql = f"SELECT * FROM {table_name} WHERE {target_col} = %s"
                cursor.execute(sql, (target_val,))
                results = cursor.fetchall()
                return self.Fetch_back(table_name,results)

    def find_data_by_keyword(self,table_name,target_col,keywaord):
        with self.connection.cursor() as cursor:
            # 查询数据
            sql = f"SELECT * FROM {table_name} WHERE {target_col} LIKE %s"
            cursor.execute(sql, (f"%{keywaord}%",))
            results = cursor.fetchall()
            return self.Fetch_back(table_name,results)

    def find_all(self,table_name):
        with self.connection.cursor() as cursor:
            # 查询数据
            sql = f"SELECT * FROM {table_name}"
            cursor.execute(sql)
            result = cursor.fetchall()
            # for row in result:
            #     print(row)
            return result

    def delete_data_by_condition(self,table_name,condition_col,Condition_val:list):
        with self.connection.cursor() as cursor:
            for query in Condition_val:
                results = self.find_data(table_name,condition_col,query[condition_col])
                if results:
                    for res in results:
                        sql = f"DELETE FROM {table_name} WHERE id=%s"
                        cursor.execute(sql, (res["id"],))
                        self.connection.commit()
                        logger.info(f"ID {res['id']}: Delete Success")

    def update_data_by_condition(self,table_name,condition_col,update_val:dict): # Paper Name as search condition

        with self.connection.cursor() as cursor:
            results = self.find_data(table_name,condition_col,update_val[condition_col])
            update_ids=[]
            if results:
                for res in results:
                     # Construct SQL query for updating
                    sql = f"UPDATE {table_name} SET {', '.join([f'{col}=%s' for col in update_val.keys()])} WHERE id=%s"
                    # Prepare update values for the query
                    update_values = [v if self.args[table_name][k] != "json" else json.dumps(v) for k, v in update_val.items()]
                    update_values.append(res["id"])
                    cursor.execute(sql, update_values)
                    self.connection.commit()
                    update_ids.append(res["id"])
                    self.Update_TimeStamp(table_name,res["id"])
            return update_ids

    def delete_data(self,table_name,condition_col,condition_val):
        with self.connection.cursor() as cursor:
            # 删除数据
            sql = f"DELETE FROM {table_name} WHERE {condition_col}=%s"
            cursor.execute(sql, (condition_val,))
            self.connection.commit()

    def drop_table(self,table_name):
        with self.connection.cursor() as cursor:
            # 删除表
            sql = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(sql)
            self.connection.commit()
            logger.info(f"Drop: {table_name} Success")

    def mysql_close(self):
        self.connection.close()

    def Update_TimeStamp(self,table_name,data_id):
        with self.connection.cursor() as cursor:
            # 更新数据
            sql = f"UPDATE {table_name} SET Finish_time=CURRENT_TIMESTAMP WHERE id=%s"
            cursor.execute(sql,(data_id,))
            self.connection.commit()


class sql_operater:
    def __init__(self,config):
        self.config=config
        self.client=mysql_db_client(config)
        self.get_task()

    def get_task(self):
        while True:
            print("""============= sql page ===============\nSql_table Operation please select actions:\n1. Search by keyword \n2. Init Table\n3. Return
                  """)
            action=input("Please select actions: ")
            if action=="1":
                self.Search_by_keyword()
            elif action=="2":
                make=input("Please type 'init table':")
                if make=="init table":
                    self.Iniitalize_Sql_table()
            elif action=="3":
                logger.info("Back To Main Page")
                break

    def Iniitalize_Sql_table(self):
        for i in self.config['sql_config']['table_name']:
            self.client.drop_table(i)
            self.client.create_table(i)
            logger.info(f"Table {i} Initialize Success")

        self.client.Show_tables()

    def Search_by_keyword(self):
        Pdf_ppt_path=input("Where to save the ppt file? ")
        Pdf_ppt_path=os.getcwd() if not os.path.isdir(Pdf_ppt_path) else Pdf_ppt_path
        keyword=input("What is the keyword? ")
        result=self.client.find_data_by_keyword("Papers_info","keywords",keyword)
        if result:
            logger.info(f"found {len(result)} results")
            Paper_list=[i["Paper_name"] for i in result]
            if os.path.exists(Pdf_ppt_path):
                make_ppt(Pdf_ppt_path,Paper_list,self.client,self.config)
        else:
            logger.debug(f"{keyword} not found in Mysql Papers_info Table")


if __name__=="__main__":
    with open('config/config.yaml', 'r') as yamlfile:
        config = yaml.safe_load(yamlfile)

    client=mysql_db_client(config)
    for i in config['sql_config']['table_name']:
        client.create_table(i)
    client.Show_tables()
    # reply_dic={'Paper_name':"test"}
    # path=input().replace('"','')
    # with open(os.path.join(path), 'rb') as file_:
        # reply_dic['pdf_file_byte'] = file_.read()
    # reply_dic={"Paper_name":"test3","keyword":"a,b,c,d"}
    # print(client.insert_data("Keyword_info","Paper_name",reply_dic))
    # reply_dic={"Paper_name":"test","keyword":"d,e,f,g"}
    # print(client.insert_data("Keyword_info","Paper_name",reply_dic))
    # reply_dic={"Paper_name":"test1","keyword":"ggg"}
    # print(client.insert_data("Keyword_info","Paper_name",reply_dic))
    # reply_dic={"Paper_name":"test2","keyword":"a,b,c,d"}
    # print(client.insert_data("Keyword_info","Paper_name",reply_dic))
    # result=client.find_data("Papers_info","Paper_name","3D2_3DSA2_1")
    # for i in result:
    #     print(i['keywords'])
    # # # print(len(result))
    # result=client.find_data_by_keyword("Image_Files","Paper_name","3DSAp1_10L")
    # for i in result:
    #     print(i['Image_id'])
    # print(client.insert_data("GPT_Cost","Project_name",{"Project_name":"test","GPT_Cost_usd":0.0001}))

    # print(client.find_data("GPT_Cost","Project_name","test"))
    # print(client.insert_data("GPT_Cost","Project_name",{"Project_name":"test","GPT_Cost_usd":0.005}))
    # print(client.find_data("GPT_Cost","Project_name","test"))

    # for i in client.find_data("Image_Files","Paper_name","3D2_3DSA2_1"):
    #     print(i['Image_id'])
    # print(client.check_exist_one("Image_Files","Paper_name","a"))
    # print(client.find_all("Papers_info"))
    # print(client.find_all("GPT_Cost"))
    # # print(client.find_all("Image_Files"))
    # for i in config['sql_config']['table_name']:
    #     client.drop_table(i)
