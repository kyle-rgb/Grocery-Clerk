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
    dag_id="kroger_scrape_promotions_cashback",
    schedule_interval="0 0 * * 2",
    start_date=pendulum.datetime(2022, 10, 25, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=210),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START docker_wakeup_call]
    @task(task_id="docker_wakeup_call")
    def docker_wakeup_call():
        import docker
        client = docker.from_env()
        if "docker-scraper-1" not in containerNames:
            scrapingContainer = list(filter(lambda x: x.name=="docker-scraper-1"), client.containers.list())[0]
            scrapingContainer.start()
            client.close()
            return 0
        else:
            client.close()
            raise AirflowSkipException
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
        scrapingContainer.exec_run("node ./src/index.js --kroger promotions cashback", user="pptruser", workdir="/app")
        return 0
    # [END kroger_operator_setup_node]
    extractTask = setup_browser_and_extract()

    # [START kroger_operator_transform_file]
    @task.virtualenv(
        task_id="virtualenv_transform_python", requirements=["pymongo==3.11.0"], system_site_packages=True
    )
    def callable_virtualenv():
        """
            Task will be performed in a virtual environment that mirrors my own environment.

            Importing at the module level ensures that it will not attempt to import the
            library before it is installed.
        """
        from pyGrocery.transformers.kroger import deconstructKrogerFiles
        
        deconstructKrogerFiles("/opt/airflow/dags/pyGrocery/tmp/")

        print("successfully started stopped node container from airflow worker in separate docker network")
        print('finished from virtual env function. exiting with status code 0.')

        return 0
    transformTask = callable_virtualenv()
    # [END kroger_operator_transform_api]

    # [START main_flow]
    wakeUpTask >> extractTask >> transformTask
    # [END main_flow]
