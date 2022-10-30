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
    # [START docker_wakeup_call]
    # TODO: Images should work in parallel for data intensive days (2/Tuesday, 6/Saturday, 0/Sunday); So Each Task Should be Able to Scrape in Parallel Given the Number of Tasks and My Own Current CPU/RAM resources
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
        scrapingContainer.exec_run("node ./src/index.js --family-dollar items", user="pptruser", workdir="/app")
        client.close()
        return 0
    # [END kroger_operator_setup_node]
    extractTask = setup_browser_and_extract()

    # [START kroger_operator_setup_node]
    @task(task_id="transform_items_data_family_dollar")
    def transform_family_dollar_item_data(ds=None, **kwargs):
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
        scrapingContainer.exec_run("node ./src/transform.js transform --family-dollar items", user="pptruser", workdir="/app")
        client.close() 
        return 0
    # [END kroger_operator_setup_node]

    transformTask = transform_family_dollar_item_data()
    # [END kroger_operator_transform_api]

    # TODO: add encrpyting and archiving to complete files after transform task was completed successfully and use EmailOperator to Send Reports.
    # TODO: past runs duration in current runs collection in MONGODB can be compared to new Dockerized/Nodeified Scraping Tasks. Sure Airflow Has its Own Version of This Too on Webserver Dashboard. 

    # [START main_flow]
    wakeUpTask >> extractTask >> transformTask
    # [END main_flow]
