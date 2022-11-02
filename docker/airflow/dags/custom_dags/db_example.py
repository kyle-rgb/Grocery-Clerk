import logging
import shutil, re
import time, datetime
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task, dag
from airflow.exceptions import AirflowSkipException
from airflow.operators.email import EmailOperator 

log = logging.getLogger(__name__)
objectId = None

with DAG(
    dag_id="db_test_dag",
    schedule_interval="0 0 * * 0",
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker", "runs", "metadata"]
) as dag:
    # [START db_try]
    @task(task_id="start_container_example")
    def start_container(command):
        import docker
        client = docker.from_env()
        # stdout will be bytes of inserted id 
        # stdout = client.containers.run("docker-scraper:latest", f"node ./src/db.js insert -f {functionName} -c runs -e airflow -d 'setting up browser for food depot items scrape'",
        # ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
        # environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
        # init=True, stdin_open=True, working_dir='/app')
        client.containers.run("docker-scraper:latest", command, working_dir='/app', tty=True, detach=True, name="scraper")
        # objectId = re.findall(r'id=([a-f0-9]+)')[0]
        return 0 
    # [END db_try]

    @task(task_id="setTimeout")
    def setTimeout(to):
        time.sleep(to)
        return 0

    @task(task_id="run-command")
    def executeCommand(data=4500):
        import docker
        client = docker.from_env()
        exit_code, output = client.containers.get("scraper").exec_run(f'node ./src/db.js test -d {data}', workdir="/app")
        output = output.decode('ascii')
        print(output)
        return exit_code

    send_email = EmailOperator(task_id="send_email_via_operator", to="kylel9815@gmail.com", subject="sent from your docker container...", html_content="""
            ## Hello From Docker !
            ### just want to inform you that all your tasks from {{task_instance.task_id}} exited cleanly and the dag run was complete for {{ ts }}.   
        """)


    start_container("/bin/sh") >> setTimeout(5) >> executeCommand() >> setTimeout(2) >> send_email



