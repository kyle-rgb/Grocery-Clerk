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
        """Starts the Browser and Runs Setup in Container"""
        pass
    # [END kroger_operator_setup_node]
    setUp = setup_browser()

    # [START kroger_operator_run_data_extraction]
    @task(task_id='extract_coupon_data_via_browser')
    def extract():
        """This function handles data extract via node script in docker network"""
        pass

    extract_task = extract()

    setUp >> sleep_task
    # [END kroger_operator_run_data_extraction]

    # [START kroger_operator_transform_api]
    if shutil.which("virtualenv"):
        log.warning("The virtualenv_python task require the virtualenv module, please install it")
    else:
        @task.virtualenv(
            task_id="virtualenv_transform_python", requirements=["pymongo==3.11.0", "pytz==2021.3"], system_site_packages=False
        )
        def callable_virtualenv():
            """
                Task will be performed in a virtual environment that mirrors my own environment.

                Importing at the module level ensures that it will not attempt to import the
                library before it is installed.
            """
            import sys

            sys.path.append("opt/***/dags")
            
            from pyGrocery.transformers.kroger import deconstructKrogerFiles
            
            deconstructKrogerFiles("/app/temp/kroger/10_18_22.json")

            print('finished from virtual env function. exiting with status code 0.')
            virtualenv_task = callable_virtualenv()
    # [END kroger_operator_transform_api]



