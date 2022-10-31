import logging
import shutil, re
import time, datetime
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task, dag
from airflow.exceptions import AirflowSkipException

log = logging.getLogger(__name__)
objectId = None

with DAG(
    dag_id="docker_test_dag",
    schedule_interval="0 0 * * 0",
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker", "runs", "metadata"]
) as dag:
    # [START db_try]
    @task(task_id="container_and_function_executor_monitor_example")
    def create_sample_run(functionName):
        import docker
        client = docker.from_env()
        # stdout will be bytes of inserted id 
        stdout = client.containers.run("docker-scraper:latest", f"node ./src/db.js insert -f {functionName} -c runs -e airflow -d 'setting up browser for food depot items scrape'",  ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
        environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
        init=True, stdin_open=True, working_dir='/app')
        stdout = stdout.decode("ascii")
        objectId = re.findall(r'id=([a-f0-9]+)')[0]
        return objectId


