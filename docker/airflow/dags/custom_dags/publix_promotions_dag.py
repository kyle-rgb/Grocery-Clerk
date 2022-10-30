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
    dag_id="publix_scrape_promotions",
    schedule_interval="0 0 * * 2",
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START docker_wakeup_call]
    @task(task_id="docker_wakeup_call")
    def docker_wakeup_call():
        # migrated current docker compose file (sans secrets) to replicate current compose network
        import docker
        client = docker.from_env()
        client.containers.run("docker-scraper-1", "node", tty=True, ports={"8081/tcp": "8080", "9229/tcp": "9229", "5900/tcp": "5900", "5000/tcp": "5000"},
        enviroment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16"},
        init=True, stdin_open=True, mounts=[
            docker.types.Mount("/app/node_modules", "browser_dependencies"),
            docker.types.Mount("/tmp/collections", "./tmp/collections/", type="bind"),
            docker.types.Mount("/app", "./scraper", type="bind")
        ], detach=True)

        return 0 
    # [END docker_wakeup_call]
    wakeUpTask = docker_wakeup_call()

    # [START kroger_operator_setup_node]
    @task(task_id="setup_browser_and_extract_data")
    def setup_browser_and_extract(ds=None, **kwargs):
        """Starts the Browser and Runs Node.js Setup in Container"""
        # has to connect to docker network running on host via docker module 
        # connect to docker and poke awake container; airflow worker should have docker module installed and access to host socket via volume
        # TODO: DOCKER_HOST env variable will be used in later versions for ssh connections to remote container instances of scraper container network.
        # run setUpBrowser from app/src/index.js with proper task argument
        # wait for confirmation of task completion, forward any logging to airflow logs
        # mark as success and move on to next task
        import docker
        client = docker.from_env()
        scrapingContainer = list(filter(lambda x: x.name=="docker-scraper-1"), client.containers.list())[0]
        scrapingContainer.exec_run("node ./src/index.js --publix promotions", user="pptruser", workdir="/app")
        return 0
    # [END kroger_operator_setup_node]
    extractTask = setup_browser_and_extract()

    # [START kroger_operator_setup_node]
    @task(task_id="transform_coupon_data_publix")
    def transform_publix_coupon_data(ds=None, **kwargs):
        """Starts the Browser and Runs Node.js Setup in Container"""
        # has to connect to docker network running on host via docker module 
        # connect to docker and poke awake container; airflow worker should have docker module installed and access to host socket via volume
        # TODO: DOCKER_HOST env variable will be used in later versions for ssh connections to remote container instances of scraper container network.
        # run setUpBrowser from app/src/index.js with proper task argument
        # wait for confirmation of task completion, forward any logging to airflow logs
        # mark as success and move on to next task
        import docker
        client = docker.from_env()
        scrapingContainer = list(filter(lambda x: x.name=="docker-scraper-1"), client.containers.list())[0]
        scrapingContainer.exec_run("node ./src/transform.js transform --publix promotions", user="pptruser", workdir="/app")
        return 0
    # [END kroger_operator_setup_node]

    transformTask = transform_publix_coupon_data()
    # [END kroger_operator_transform_api]

    # [START main_flow]
    wakeUpTask >> extractTask >> transformTask
    # [END main_flow]
