import logging
import shutil
import time, datetime
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task, dag
from airflow.exceptions import AirflowSkipException

log = logging.getLogger(__name__)

with DAG(
    dag_id="family_dollar_scrape_items",
    schedule_interval="0 0 * * 6", # runs every saturday, the last turnover date before next publicized promotion date (as given by their weekly ads)
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START db_try]
    @task(task_id="start_container_example")
    def start_container():
        import docker
        client = docker.from_env()

        container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name="scraper",
                ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
                environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
                init=True, stdin_open=True
            )

        return 0 
    # [END db_try]

    @task(task_id="insert-run")
    def insertRun(functionName=None, description=None, args=None, ti=None):
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
        if not args:
            args = {}

        args["pre_execute_stats"] = container.stats(stream=False)
        baseCmd += f" --args '{json.dumps(args)}'"
        print("executing $ ", baseCmd)
        code, output = container.exec_run(cmd=baseCmd,
            user="pptruser", environment={"MONGO_CONN_URL": connections["MONGO_CONN_URL"].get_uri()},
            workdir="/app"
        )
        output = output.decode("ascii")
        print(output)
        output = re.findall(r"id=([a-f0-9]+)", output)[0]
        ti.xcom_push(key="run_object_id", value=output)
        return 0

    @task(task_id="update-run")
    def updateRun(functionName=None, args=None, push=False, description=None, ti=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json 
        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get("scraper")
        _id = ti.xcom_pull(key="run_object_id", task_ids="insert-run")
        # at base level closes the loop on the returning function, then consults kwargs on whether to add to run stack 
        stats = json.dumps(container.stats(stream=False))
        baseCmd = f"node ./src/db.js insert -c runs -e airflow -i {_id} -s '{stats}'"
        
        if push:
            baseCmd += f" -f {functionName} -d '{description}' --args '{json.dumps(args)}' --push"
        print("executing $ ", baseCmd)
        code, output = container.exec_run(cmd=baseCmd,
        user="pptruser", environment={"MONGO_CONN_URL": connections["MONGO_CONN_URL"].get_uri()},
        workdir="/app")
        output = output.decode("ascii")
        print(output)
        return 0

    @task(task_id="scrape_dataset")
    def scrape_dataset(chain=None, target_data=None, add_args=None):
        import docker
        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get("scraper")
        if chain=="kroger" and target_data=="promotions" and add_args:
            target_data += add_args
        code, output = container.exec_run(f"node ./src/index.js scrape --{chain} {target_data}", workdir="/app", user="pptruser")
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
        logs = client.containers.get("scraper").logs(stream=False)
        logs = logs.decode("ascii")
        print(logs)
        client.containers.get("scraper").remove(force=True)
        print('container stopped')
        return 0


    send_email = EmailOperator(task_id="send_email_via_operator", to="kylel9815@gmail.com", subject="sent from your docker container...", html_content="""
            <h1>Hello From Docker !</h1>
            <h3>just want to inform you that all your tasks from {{run_id}} exited cleanly and the dag run was complete for {{ ts }}.</h3>   
        """)

    start_container() >> [insertRun("getFamilyDollarItems", "get family dollar's internal item data from own website"), scrape_dataset("family-dollar", "items")] >> updateRun(push=False) >> stop() >> send_email