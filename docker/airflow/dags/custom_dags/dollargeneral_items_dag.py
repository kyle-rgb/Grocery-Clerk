import logging
import shutil, re
import time, datetime
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task, dag
from airflow.exceptions import AirflowSkipException
from airflow.operators.email import EmailOperator 
from airflow.operators.bash import BashOperator

log = logging.getLogger(__name__)
default_args = {
    "chain": "dollar-general",
    "target_data": "items",
    "docker_name": "scraper_dg_items"
}

with DAG(
    dag_id="dollar_general_scrape_items",
    schedule_interval="0 0 * * 6", # runs every saturday, the last turnover date before next publicized promotion date (as given by their weekly ads)
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    default_args=default_args,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker", "runs", "metadata"]
) as dag:
    # [START db_try]
    @task(task_id="start_container")
    def start_container(docker_name=None):
        import docker
        from airflow.secrets.local_filesystem import load_variables
        
        email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]
        client = docker.from_env()


        container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name=docker_name,
                ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
                environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16", "EMAIL": email},
                init=True, stdin_open=True,
                privileged =True
            )
        client.close()

        return 0 
    # [END db_try]

    @task(task_id="insert-run")
    def insertRun(functionName=None, description=None, args=None, docker_name=None, ti=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json, re

        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get(docker_name)
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
    def updateRun(functionName=None, args=None, push=False, docker_name=None, description=None, ti=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json 
        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get(docker_name)
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
    def scrape_dataset(chain=None, target_data=None, docker_name=None, add_args=None):
        import docker
        from airflow.secrets.local_filesystem import load_variables
        client = docker.from_env()
        var_dict = load_variables("/run/secrets/secrets-vars.json")


        client = docker.from_env()
        container = client.containers.get(docker_name)
        if chain=="kroger" and target_data=="promotions" and add_args:
            target_data += add_args
        code, output = container.exec_run(f"node ./src/index.js scrape --{chain} {target_data}", workdir="/app", user="pptruser",
        environment={"ZIPCODE": var_dict["ZIPCODE"], "PHONE_NUMBER": var_dict["PHONE_NUMBER"], "KROGER_USERNAME": var_dict["KROGER_USERNAME"], "KROGER_PASSWORD": var_dict["KROGER_PASSWORD"]})
        output = output.decode("ascii")
        print(output)
        if "error" in output:
            return 1
        else :
            return 0

    @task(task_id="setTimeout")
    def setTimeout(to):
        time.sleep(to)

        return 0

    @task(task_id="run-command")
    def executeCommand(data=4500, docker_name=None):
        import docker
        client = docker.from_env()
        exit_code, output = client.containers.get(docker_name).exec_run(f'node ./src/db.js test -d {data}', workdir="/app")
        output = output.decode('ascii')
        print(output)
        return exit_code

    @task(task_id="stop-container")
    def stop(docker_name=None):
        import docker
        client = docker.from_env()
        logs = client.containers.get(docker_name).logs(stream=False)
        logs = logs.decode("ascii")
        print(logs)
        client.containers.get(docker_name).stop()
        print('container stopped')
        return 0


    send_email = EmailOperator(task_id="send_email_via_operator", to="kylel9815@gmail.com", subject="sent from your docker container...", html_content="""
            <h1>Hello From Docker !</h1>
            <h3>just want to inform you that all your tasks from {{run_id}} exited cleanly and the dag run was complete for {{ ts }}.</h3>   
        """)

    docker_cp_bash = BashOperator(task_id="bash_docker_cp", bash_command=f"docker cp {default_args['docker_name']}:/app/tmp/collections /tmp/archive/")

    @task(task_id="transform-data")
    def transformData(chain=None, target_data=None, docker_name=None):
        # legal values for chain = food-depot, family-dollar, aldi, publix, dollar-general
        # legal values for target_data = items, instacartItems, promotions
        import docker
        from airflow.secrets.local_filesystem import load_variables, load_connections_dict
        client = docker.from_env()
        email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]
        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        container = client.containers.get(docker_name)
        baseCmd = f"node ./src/transform.js transform --{chain} {target_data}"
        print("executing $ ", baseCmd)
        code, output = container.exec_run(cmd=baseCmd,
            user="pptruser", environment={"MONGO_CONN_URL": connections["MONGO_CONN_URL"].get_uri(), "EMAIL": email},
            workdir="/app"
        )
        output = output.decode("ascii")
        print(output)
        client.close()

        return 0

    @task(task_id="archive_data")
    def archiveData(chain=None, target_data=None, docker_name=None):
        # legal values for chain = food-depot, family-dollar, aldi, publix, dollar-general
        # legal values for target_data = items, instacartItems, promotions
        import docker
        from airflow.secrets.local_filesystem import load_variables
        client = docker.from_env()
        email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]

        container = client.containers.get(docker_name)
        no_space_path = chain.replace("-", "")
        baseCmd = f"node ./src/transform.js compress --path /app/tmp/collections/{no_space_path}"
        print("executing $ ", baseCmd)
        code, output = container.exec_run(cmd=baseCmd,
            user="pptruser", environment={"EMAIL": email},
            workdir="/app"
        )
        output = output.decode("ascii")
        print(output)
        client.close()

        return 0

    start_container() >> insertRun("".join(["get", default_args["chain"].title(), default_args["target_data"].title()]), f"get {default_args['chain']} {default_args['target_data']} data") >> scrape_dataset() >> updateRun(functionName=f"transform{default_args['chain'].title()}", args=default_args, push=True, description=f"transform {default_args['chain']}s {default_args['target_data']} data")  >> transformData() >> updateRun(push=False) >> archiveData() >> docker_cp_bash >> stop() >> send_email
