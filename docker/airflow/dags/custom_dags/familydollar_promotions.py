import logging
import shutil
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
    "chain": "family-dollar",
    "target_data": "promotions",
    "docker_name": "scraper_fd_promotions"
}


with DAG(
    dag_id="family_dollar_scrape_promotions",
    schedule_interval="0 0 * * 6", # runs every saturday, the last turnover date before next publicized promotion date (as given by their weekly ads)
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    default_args=default_args,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START db_try]
    @task(task_id="start_container")
    def start_container(docker_name=None):
        import docker, shutil
        from airflow.secrets.local_filesystem import load_variables
        
        email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]
        client = docker.from_env()


        container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name=docker_name,
                ports={ "5900/tcp": None },
                environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16", "EMAIL": email},
                init=True, stdin_open=True,
                privileged =True
            )
        client.close()

        return 0 
    # [END db_try]

    @task(task_id="insert-run")
    def insertRun(pipeline_action="scrape", description=None, args={}, docker_name=None, chain=None, target_data=None, ti=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json, re

        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get(docker_name)
        baseCmd = "node ./src/db.js insert -c runs -e airflow"
        functionName = pipeline_action + chain.title() + target_data.title() 
        description = description or pipeline_action +" "+ chain.title() + target_data.title() 
        args["pre_execute_stats"] = container.stats(stream=False) 
        baseCmd += f" -f {functionName} -d {description} --args '{json.dumps(args)}' " 
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
    def updateRun(pipeline_action="scrape", args={}, push=False, docker_name=None, description=None, chain=None, target_data=None, ti=None):
        import docker
        from airflow.secrets.local_filesystem import load_connections_dict
        from pprint import pprint
        import json 
        connections = load_connections_dict("/run/secrets/secrets-connections.json")

        client = docker.from_env()
        container = client.containers.get(docker_name)
        _id = ti.xcom_pull(key="run_object_id", task_ids="insert-run")
        # at base level closes the loop on the returning function, then consults kwargs on whether to add to run stack
        # represents the final stats dealing with container
        stats = json.dumps(container.stats(stream=False))
        baseCmd = f"node ./src/db.js insert -c runs -e airflow -i {_id} -s '{stats}'"
        
        if push:
            functionName = pipeline_action + chain.title()+target_data.title()
            description = description or (pipeline_action +" "+ chain+"s " + target_data + " data")
            args["pre_execute_stats"] = container.stats(stream=False)
            baseCmd += f" -f {functionName} -d '{description}' --args '{json.dumps(args)}' --push"
        print("executing $ ", baseCmd)
        code, output = container.exec_run(cmd=baseCmd,
            user="pptruser", environment={"MONGO_CONN_URL": connections["MONGO_CONN_URL"].get_uri()},
            workdir="/app"
        )
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
            target_data += " " + add_args
        code, output = container.exec_run(f"node ./src/index.js scrape --{chain} {target_data}", workdir="/app", user="pptruser",
            environment={"ZIPCODE": var_dict["ZIPCODE"], "PHONE_NUMBER": var_dict["PHONE_NUMBER"], "KROGER_USERNAME": var_dict["KROGER_USERNAME"], "KROGER_PASSWORD": var_dict["KROGER_PASSWORD"]}
        )
        output = output.decode("ascii")
        print(output)
        if "error" in output:
            return 1
        else :
            return 0

    

    @task(task_id="stop-container")
    def stop(docker_name=None):
        import docker
        client = docker.from_env()
        container = client.containers.get(docker_name) 
        logs = container.logs(stream=False)
        logs = logs.decode("ascii")
        print(logs)
        # rm tmp lock file to all for x11 re-entry for inspection of container files post a run
        code, output = container.exec_run(cmd="rm /tmp/.X1-lock -f") 
        output = output.decode("ascii")
        print(output)
        container.stop()
        print('container stopped')
        client.close()
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

    start_container() >> insertRun() >> scrape_dataset() >> updateRun(pipeline_action="transform", push=True)  >> transformData() >> updateRun(pipeline_action="archive", push=True) >> archiveData() >> docker_cp_bash >> updateRun(push=False)>> stop() >> send_email