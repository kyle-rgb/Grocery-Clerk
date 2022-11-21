from datetime import timedelta
import pendulum, logging

from airflow.decorators import task, dag
from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.email import EmailOperator 
from airflow.operators.bash import BashOperator

configs = {
    "aldi": {
        "items": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 2",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["aldi", "items", "instacart"]
            }
        }
    },
    "publix": {
        "items" : {
            "dag_vars": {
                "schedule_interval": "0 0 * * 2",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["publix", "items", "instacart"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 2",
                "dagrun_timeout": timedelta(minutes=10),
                "tags": ["publix", "promotions", "1st Party Site"]
            }
        }
    },
    "kroger": {
        "promotions": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 2",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["kroger", "promotions", "1st Party Site"]
            }
        },
        "trips": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 3",
                "dagrun_timeout": timedelta(minutes=45),
                "tags": ["kroger", "trips", "1st Party Site"]
            }
        }
    },
    "familyDollar": {
        "items": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 6",
                "dagrun_timeout": timedelta(minutes=120),
                "tags": ["family dollar", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 6",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["family dollar", "promotions", "1st Party Site"]
            }
        },
        "instacartItems": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 6",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["family dollar", "items", "instacart"]
            }
        }
    },
    "dollarGeneral": {
        "items": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 6",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["dollar general", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 6",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["dollar general", "promotions", "1st Party Site"]
            }
        }
    },
    "foodDepot": {
        "items": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 0",
                "dagrun_timeout": timedelta(minutes=300),
                "tags": ["food depot", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 0",
                "dagrun_timeout": timedelta(minutes=30),
                "tags": ["food depot", "promotions", "1st Party Site"]
            }
        }
    }
}

for chain, dag_types in configs.items():

    for target_data, setup_vars in dag_types.items():
        kwargs = setup_vars["dag_vars"]
        kwargs["default_args"] = {"target_data": target_data, "chain": chain, "docker_name": f"scraper_{chain}_{target_data}"}
        kwargs["tags"] += ["grocery", "GroceryClerk", "ETL", "python", "node", "mongodb", "docker"]
    
        dag_id = f"dynamic_generated_dag_scrape_{chain}_{target_data}"
        log = logging.getLogger(__name__)

        @dag(
            dag_id=dag_id,
            start_date=pendulum.datetime(2022, 11, 20, tz="UTC"),
            catchup=False,
            **kwargs
        )
        def dynamic_generated_dag():
            # [START db_try]
            @task(task_id="start_container")
            def start_container(docker_name=None):
                import docker, shutil
                from airflow.secrets.local_filesystem import load_variables
                
                email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]
                client = docker.from_env()
                container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name=docker_name,
                        ports={
                            # "8081/tcp": "8081",
                            # "9229/tcp": "9229",
                            "5900/tcp": None # mapping for xvnc 
                            #"5000/tcp": "5000" # only use case for temporary space for spin up server in food depot promotions confirmation via iphone shortcut 
                        },
                        environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16", "EMAIL": email},
                        init=True, stdin_open=True,
                        privileged =True
                )

                client.close()

                return 0 
                
            start_container()
            # [END db_try]

        globals()[dag_id] = dynamic_generated_dag()