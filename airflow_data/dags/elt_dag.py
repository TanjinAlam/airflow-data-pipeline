# from datetime import datetime
# from airflow import DAG
# from helper.utils import my_function
# # from docker.types import Mount

# # from airflow.providers.docker.operators.docker import DockerOperator
# from airflow.utils.dates import days_ago
# # from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
# from airflow.operators.python import PythonOperator

# CONN_ID = 'c8a9cedc-07c0-4201-9576-7df29fa40c94'


# default_args = {
#     'owner': 'airflow',
#     'depends_on_past': False,
#     'email_on_failure': False,
#     'email_on_retry': False,
# }


# # def run_elt_script():
# #     script_path = "/opt/airflow/elt_script/elt_script.py"
# #     result = subprocess.run(["python", script_path],
# #                             capture_output=True, text=True)
# #     if result.returncode != 0:
# #         raise Exception(f"Script failed with error: {result.stderr}")
# #     else:
# #         print(result.stdout)


# dag = DAG(
#     'mongo_pipeline',
#     default_args=default_args,
#     description='An ELT workflow with mongo',
#     start_date=datetime(2023, 10, 3),
#     catchup=False,
# )

# # Need to change this to be an Airbyte DAG instead
# # t1 = AirbyteTriggerSyncOperator(
# #     task_id='airbyte_postgres_postgres',
# #     airbyte_conn_id='airbyte',
# #     connection_id=CONN_ID,
# #     asynchronous=False,
# #     timeout=3600,
# #     wait_seconds=3,
# #     dag=dag
# # )

# t1 = PythonOperator(
#     task_id='print',
#     python_callable= my_function,
#     op_kwargs = {"x" : "Apache Airflow"},
#     dag=dag,
# )

# # t2 = DockerOperator(
# #     task_id='dbt_run',
# #     image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
# #     command=[
# #         "run",
# #         "--profiles-dir",
# #         "/root",
# #         "--project-dir",
# #         "/dbt",
# #         "--full-refresh"
# #     ],
# #     auto_remove=True,
# #     docker_url="unix://var/run/docker.sock",
# #     network_mode="bridge",
# #     mounts=[
# #         Mount(source='/Users/piash/Data-Engineering/elt/custom_postgres',
# #               target='/dbt', type='bind'),
# #         Mount(source='/Users/piash/.dbt', target='/root', type='bind'),
# #     ],
# #     dag=dag
# # )


# t1 



import os
import json
import time
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.http.operators.http import SimpleHttpOperator, HttpOperator
from airflow.providers.http.sensors.http import HttpSensor
from datetime import datetime,timedelta
#import Mongo hook from airflow
from airflow.providers.mongo.hooks.mongo import MongoHook
from dotenv import load_dotenv
import pymongo
load_dotenv()

def inset_mong_using_pyMongo(**context):
    try:
        print(" I AM HERE",context["result"])

        mongo_host = os.getenv("MONGO_HOST")
        mongo_port = os.getenv("MONGO_PORT")  
        mongo_user = os.getenv("MONGO_USER")      
        mongo_pass = os.getenv("MONGO_PASS")
        const_conn_str = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/admin?retryWrites=true&w=majority"
        client = pymongo.MongoClient(const_conn_str, serverSelectionTimeoutMS=5000)
        db = client["dtcc-cftc-data"]['currency']
        db.insert_one(context["result"])
    except Exception as e:
        print("Error connecting to MongoDB --",e)

def calculateDV01(**context):
  
    try:
        ti = context['ti']
        data = ti.xcom_pull(task_ids='find_last_six_month_data')
        for i in data:
            print("adsasdasdasd", i)   
    #         # expiration_date = pd.to_datetime(df['Expiration Date'][0])
    #         # today_date = pd.to_datetime(datetime.today().date())
    #         # effective_date = pd.to_datetime(df['Effective Date'][0])
    #         # notional = float(df['Notional amount-Leg 1'][0].replace(',',''))
    #         # eur_usd = 1.084
    #         # dv01 = (((expiration_date - max(today_date,effective_date)).days)*notional*eur_usd)/(365*10000)      
    except Exception as e:
        print("Error connecting to MongoDB --",e)

def find_last_six_month_data():
    try:
        mongo_url = os.getenv("MONGO_URL")
        start_date = datetime.now() - timedelta(days=180)
        start_date = start_date.strftime('%Y-%m-%d')
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = client["dtcc-cftc-data"]['rates']
        db.create_index([("Execution Timestamp", pymongo.DESCENDING)])
        last_six_month_data = list(db.find( {"Execution Timestamp": {"$gte": "2024-01-13"}}, {"Expiration Date": 1, "Effective Date": 1, "Notional amount-Leg 1": 1, "_id": 0}).batch_size(5000))
        return last_six_month_data
    except Exception as e:
        print("Error connecting to MongoDB --",e)
        
def uploadtomongo(ti, **context):
    try:
        mongo_host = os.getenv("MONGO_HOST")
        mongo_port = os.getenv("MONGO_PORT")  
        mongo_user = os.getenv("MONGO_USER")      
        mongo_pass = os.getenv("MONGO_PASS")
        const_conn_str = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/admin?retryWrites=true&w=majority"
        client = pymongo.MongoClient(const_conn_str, serverSelectionTimeoutMS=5000)
        db = client["dtcc-cftc-data"]['currency']
        db.insert_one(context["result"])
    except Exception as e:
        print("Error connecting to MongoDB --",e)

with DAG(
    dag_id="load_currency_data",
    schedule_interval='@Daily',
    start_date=datetime(2024, 2, 22),
    catchup=False,
    tags= ["currency"],
    default_args={
        "owner": "Rob",
        "retries": 2,
        "retry_delay": timedelta(microseconds=3000)
    }
) as dag:
    
    t1_is_active = HttpSensor(
        task_id='is_currency_api_active',
        http_conn_id='currency_api',
        endpoint='USD',
    )

    t1 = HttpOperator(
        http_conn_id='currency_api',
        task_id='get_currency',
        method='GET',
        endpoint='USD',
        response_filter=lambda response: response.json(),
        headers={"Content-Type": "application/json"},
        log_response=True,
        do_xcom_push=True,
        dag=dag)
    
    t2 = PythonOperator(
        task_id='upload-mongodb',
        python_callable=uploadtomongo,
        op_kwargs={"result": t1.output},
        dag=dag
        )
    
    t3 = PythonOperator(
        task_id='find_last_six_month_data',
        python_callable=find_last_six_month_data,
        dag=dag
    )
    
    t4 = PythonOperator(
        task_id='insert_mongo',
        python_callable=calculateDV01,
        dag=dag
    )
    
    # t1_is_active >> t1 >> t2 >> t3
    t3 >> t4 
    
    
