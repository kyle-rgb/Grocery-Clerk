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
    def start_container():
        import docker, datetime as dt
        client = docker.from_env()
        # stdout will be bytes of inserted id 
        # stdout = client.containers.run("docker-scraper:latest", f"node ./src/db.js insert -f {functionName} -c runs -e airflow -d 'setting up browser for food depot items scrape'",
        # ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
        # environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
        # init=True, stdin_open=True, working_dir='/app')
        container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name="scraper",
                ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
                environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
                init=True, stdin_open=True
            )
        try:
            logs = container.logs(stream=True, follow=True)
            logLine = bytearray()
            while True:
                line = next(logs)
                if line != b'\n':
                    logLine.extend(line)
                else:
                    logLine = logLine.decode("ascii")
                    print(logLine)
                    logLine = bytearray()
        except StopIteration:
            print(f'log stream ended for scraper')
        finally:
            client.close()
        return 0 
    # [END db_try]

    @task(task_id="insert-run")
    def insertRun(push=False, functionName=None, description=None, args=None, ti=None, run_id=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json 

        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get("scraper")
        baseCmd = "node ./src/db.js insert -c runs -e airflow"
        if functionName:
            baseCmd += " -f " + functionName
        if description:
            baseCmd += f" -d '{description}'"
        if push:
            baseCmd += f" -i {run_id} --push"
        if args:
            baseCmd += f" --args {json.dumps(args)}"

        code, output = container.exec_run(cmd=baseCmd,
        user="pptruser", environment={"MONGO_CONN_URL": connections["MONGO_CONN_URL"].get_uri()},
        workdir="/app")
        output = output.decode("ascii")
        print(output)
        return 0

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

    @task(task_id="stop-container")
    def stop():
        import docker
        client = docker.from_env()
        logged = client.containers.get("scraper").logs(stream=False)
        print(logged)
        client.containers.get("scraper").remove(force=True)
        print('container stopped')
        return 0


    send_email = EmailOperator(task_id="send_email_via_operator", to="kylel9815@gmail.com", subject="sent from your docker container...", html_content="""
            <h1>Hello From Docker !</h1>
            <h3>just want to inform you that all your tasks from {{task_instance.task_id}} exited cleanly and the dag run was complete for {{ ts }}.</h3>   
        """)

    # @task.virtualenv(
    #     task_id="virtualenv_python", requirements=["pymongo==3.11.0"], system_site_packages=True
    # )
    # def callable_virtualenv():
    #     """
    #         Task will be performed in a virtual environment that mirrors my own environment.

    #         Importing at the module level ensures that it will not attempt to import the
    #         library before it is installed.
    #     """
    #     from pymongo import MongoClient
    #     from airflow.secrets.local_filesystem import load_connections_dict
    #     from pprint import pprint

    #     connections = load_connections_dict("/run/secrets/secrets-connections.json")
    #     uri = connections["MONGO_CONN_URL"].get_uri()
    #     client = MongoClient(uri)
    #     cursor = client["new"]
    #     res = cursor["items"].find({}).limit(1)
    #     for r in res:
    #         pprint(r)
        
    #     return 0 

    # start_container("/bin/sh") 
    # setTimeout(5) >> executeCommand() >> setTimeout(2) >> stop() >> send_email
    start_container()
    setTimeout(7) >> insertRun(functionName='test1', description='testing from container-1') >> setTimeout(2) >> insertRun(_id=objectId, functionName="test1") >> stop() >> send_email

