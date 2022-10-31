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
    dag_id="docker_test_dag",
    schedule_interval="0 0 * * 0",
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START docker_wakeup_call]
    # recreate features defined in docker compose file 
    @task(task_id="docker_wakeup_call")
    def docker_wakeup_call():
        # migrated current docker compose file (sans secrets) to replicate current compose network
        import docker, time
        client = docker.from_env()
        container = client.containers.run("docker-scraper:latest", "node -e 'console.log(Math.PI)'",  ports={"8081/tcp": "8081", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
        environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
        init=True, stdin_open=True, working_dir='/app', detach=True
        #mounts=[
            # docker.types.Mount("/app", "/scraper", type="bind"),
            # docker.types.Mount("/app/node_modules", "browser_dependencies"),
            # docker.types.Mount("/tmp/collections", "/tmp/collections/", type="bind"),       
        # ]
        )
        print(container.logs())
        for i in range(4):
            print("slept for ", i)
            time.sleep(1)

        container.remove(force=True)
        client.close()
        print("removed container and closed client")        
        return 0 
    # [END docker_wakeup_call]
    wakeUpTask = docker_wakeup_call()