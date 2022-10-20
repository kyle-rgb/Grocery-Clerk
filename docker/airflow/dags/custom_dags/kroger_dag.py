import logging
import shutil
import time
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task, dag

log = logging.getLogger(__name__)

with DAG(
    dag_id="kroger_",
    schedule_interval=None,
    start_date=pendulum.datetime(2022, 10, 18, tz="UTC"),
    catchup=False,
    tags=["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
) as dag:
    # [START kroger_operator_setup_node]
    @task(task_id="setup_browser")
    def setup_browser(ds=None, **kwargs):
        """Starts the Browser and Runs Node.js Setup in Container"""
        # has to connect to docker network running on host via docker module 
        # connect to docker and poke awake container; airflow worker should have docker module installed and access to host socket via volume
        # TODO: DOCKER_HOST env variable will be used in later versions for ssh connections to remote container instances of scraper container network.
        # run setUpBrowser from app/src/index.js with proper task argument
        # wait for confirmation of task completion, forward any logging to airflow logs
        # mark as success and move on to next task
        time.sleep(1)
        return 0
    # [END kroger_operator_setup_node]
    setUpTask = setup_browser()

    # [START kroger_operator_run_data_extraction]
    @task(task_id='extract_coupon_data_via_container_browser')
    def extract():
        """ This function handles data extract via Node.js script in Docker network."""
        # attach back to successfully handled browser and run core extraction script -> (getKrogerCoupons, getKrogerTrips)

        # forward logs to airflow, monitor container health & resorces and wait for completion 

        # on completion, file for date should show in proper folder

        # mark as success and move on to python decomposition of created file
        print("passed through kroger-operator-run-data-extraction")
        time.sleep(2)
        return 0

    extractTask = extract()

    # [END kroger_operator_run_data_extraction]

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
        
        print("correctly loaded transformer package in virtual env", deconstructKrogerFiles)
        
        deconstructKrogerFiles("./dags/pyGrocery/10_11_2022.json")

        import docker

        client = docker.from_env()
        containerNames = list(map(lambda x: x.name, client.containers.list(all=True))) # to get stopped containers
        print("Containers running on my Windows 10 Host : ", containerNames)
        myContainer = client.containers.list(all=True)[0]
        myContainer.start()
        print("successfully started stopped node container from airflow worker in separate docker network")
        print('finished from virtual env function. exiting with status code 0.')

        return 0
    transformTask = callable_virtualenv()
    # [END kroger_operator_transform_api]

    # [START main_flow]
    setUpTask >> extractTask >> transformTask
    # [END main_flow]
