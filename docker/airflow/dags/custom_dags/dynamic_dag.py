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
                "schedule_interval": "5 0 * * 2,3",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["aldi", "items", "instacart"]
            }
        }
    },
    "publix": {
        "items" : {
            "dag_vars": {
                "schedule_interval": "0 19 * * 1,2",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["publix", "items", "instacart"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "3 0 * * 2,3",
                "dagrun_timeout": timedelta(minutes=10),
                "tags": ["publix", "promotions", "1st Party Site"]
            }
        }
    },
    "kroger": {
        "special": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 2,3",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["kroger", "promotions", "1st Party Site"]
            }
        },
        "digital": {
            "dag_vars": {
                "schedule_interval": "1 0 * * 2,3",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["kroger", "promotions", "1st Party Site"]
            }
        },
        "cashback": {
            "dag_vars": {
                "schedule_interval": "2 0 * * 2,3",
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
    "family-dollar": {
        "items": {
            "dag_vars": {
                "schedule_interval": "3 0 * * 6,0",
                "dagrun_timeout": timedelta(minutes=120),
                "tags": ["family dollar", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "2 0 * * 6,0",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["family dollar", "promotions", "1st Party Site"]
            }
        },
        "instacartItems": {
            "dag_vars": {
                "schedule_interval": "1 0 * * 6,0",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["family dollar", "items", "instacart"]
            }
        }
    },
    "dollar-general": {
        "items": {
            "dag_vars": {
                "schedule_interval": "5 0 * * 6,0",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["dollar general", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "8 0 * * 6,0",
                "dagrun_timeout": timedelta(minutes=500),
                "tags": ["dollar general", "promotions", "1st Party Site"]
            }
        }
    },
    "food-depot": {
        "items": {
            "dag_vars": {
                "schedule_interval": "0 0 * * 0",
                "dagrun_timeout": timedelta(minutes=300),
                "tags": ["food depot", "items", "1st Party Site"]
            }
        },
        "promotions": {
            "dag_vars": {
                "schedule_interval": "1 0 * * 0",
                "dagrun_timeout": timedelta(minutes=30),
                "tags": ["food depot", "promotions", "1st Party Site"]
            }
        }
    }
}

for chain, dag_types in configs.items():

    for target_data, setup_vars in dag_types.items():
        kwargs = setup_vars["dag_vars"]
        kwargs["default_args"] = {"target_data": target_data, "chain": chain, "docker_name": f"scraper_{chain}_{target_data}",
        "email_on_failure": True, "email": "kylel9815@gmail.com", "retries": 4, "retry_delay": timedelta(seconds=60)}
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
            @task(task_id="start_container")
            def start_container(docker_name=None, chain=None, target_data=None, email_on_failure=None):
                import docker, shutil
                from airflow.secrets.local_filesystem import load_variables
                
                var_dict = load_variables("/run/secrets/secrets-vars.json")
                email = var_dict["EMAIL"]
                if chain == 'kroger' and target_data == 'trips':
                    extra_env = {"USERNAME_KROGER": var_dict["KROGER_USERNAME"], "PASSWORD_KROGER": var_dict["KROGER_PASSWORD"]}
                else:
                    extra_env = {}

                client = docker.from_env()
                if chain=="food-depot" and target_data=="promotions":
                    extra_ports = {"5000/tcp": "5000"} # only use case for temporary space for spin up server in food depot promotions confirmation via iphone shortcut
                else:
                    extra_ports = {} 
                container = client.containers.run("docker-scraper:latest", working_dir='/app', detach=True, name=docker_name,
                        ports={
                            "5900/tcp": None, # mapping for xvnc 
                            **extra_ports  
                        },
                        environment={"GPG_TTY": "/dev/pts/0", "DISPLAY": ":1", "XVFB_RESOLUTION": "1920x1080x16", "EMAIL": email, **extra_env},
                        init=True, stdin_open=True,
                        privileged =True
                )

                client.close()

                return 0
            
            @task(task_id="stop_container")
            def stopContainer(docker_name=None):
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
                
            @task(task_id="insert_run")
            def insertRun(pipeline_action="scrape", description=None, args={}, docker_name=None, chain=None, target_data=None, ti=None, email_on_failure=None):
                import docker
                from airflow.secrets.local_filesystem import load_connections_dict
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

            @task(task_id="update_run")
            def updateRun(pipeline_action="scrape", args={}, push=False, docker_name=None, description=None, chain=None, target_data=None, ti=None, email_on_failure=None):
                import docker
                from airflow.secrets.local_filesystem import load_connections_dict
                import json 
                connections = load_connections_dict("/run/secrets/secrets-connections.json")

                client = docker.from_env()
                container = client.containers.get(docker_name)
                _id = ti.xcom_pull(key="run_object_id", task_ids="insert_run")
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
            def scrapeData(chain=None, target_data=None, docker_name=None, email_on_failure=None):
                import docker
                from airflow.secrets.local_filesystem import load_variables
                client = docker.from_env()
                var_dict = load_variables("/run/secrets/secrets-vars.json")


                client = docker.from_env()
                container = client.containers.get(docker_name)
                if (chain=="kroger") and (target_data=="digital" or target_data=="cashback"):
                    target_data = f" promotions --type {target_data}"
                code, output = container.exec_run(f"node ./src/index.js scrape --{chain} {target_data}", workdir="/app", user="pptruser",
                    environment=var_dict
                )
                try:
                    output = output.decode("ascii")
                except UnicodeDecodeError:
                    output = output.decode("ascii", errors="replace") 
                print(output)
                if code != 0:
                    raise ValueError("return code from container was not null : ", code)
                else :
                    return 0

            @task(task_id="transform_data_via_node")
            def transformData(chain=None, target_data=None, docker_name=None, email_on_failure=None):
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

            @task.virtualenv(
                task_id="transform_data_via_python_virtualenv", requirements=["pymongo==3.11.0"], system_site_packages=True
            )
            def transformDataVenv(chain, target_data, email_on_failure=None):
                """
                    Task will be performed in a virtual environment that mirrors my own environment.

                    Importing at the module level ensures that it will not attempt to import the
                    library before it is installed.
                """
                from pyGrocery.transformers.kroger import deconstructKrogerFile
                import os, shutil
                from airflow.secrets.local_filesystem import load_connections_dict

                connections = load_connections_dict("/run/secrets/secrets-connections.json")
                os.environ["MONGO_CONN_URL"] = connections["MONGO_CONN_URL"].get_uri()

                tempFiles = [os.path.join(folder, file) for folder, __, files in os.walk("/tmp/archive/.venv_files/collections/kroger/") for file in files]
                if len(tempFiles)==0:
                    raise ValueError("/tmp/archive/.venv_files is empty")
                for tempFile in tempFiles:
                    deconstructKrogerFile(tempFile)

                print("successfully transformed promotions files in python venv")
                shutil.rmtree("/tmp/archive/.venv_files/collections/kroger")
                print("cleaned up tmp files in archive volume")


                return 0

            @task(task_id="archive_data")
            def archiveData(chain=None, target_data=None, docker_name=None, email_on_failure=None):
                # legal values for chain = food-depot, family-dollar, aldi, publix, dollar-general
                # legal values for target_data = items, instacartItems, promotions
                import docker
                from airflow.secrets.local_filesystem import load_variables
                client = docker.from_env()
                email = load_variables("/run/secrets/secrets-vars.json")["EMAIL"]

                container = client.containers.get(docker_name)
                no_space_path = chain.replace("-", "").lower()
                baseCmd = f"node ./src/transform.js compress --path /app/tmp/collections/{no_space_path} --name {docker_name}"
                print("executing $ ", baseCmd)
                code, output = container.exec_run(cmd=baseCmd,
                    user="pptruser", environment={"EMAIL": email},
                    workdir="/app"
                )
                output = output.decode("ascii")
                print(output)
                client.close()

                return 0
            

            send_email = EmailOperator(task_id="send_email_via_operator", to="kylel9815@gmail.com", subject="sent from your docker container...",
            html_content="""
                    <h1>Hello From Docker !</h1>
                    <h3>just want to inform you that all your tasks from {{run_id}} exited cleanly and the dag run was complete for {{ task_instance_key_str }}.</h3>
                    <h4>{{params.docker_name}}</h4>   
            """, params=kwargs["default_args"])

            docker_cp_bash = BashOperator(task_id="bash_docker_cp", bash_command=f"docker cp {kwargs['default_args']['docker_name']}:/app/tmp/collections /tmp/archive/")

            # [START main_flow_non_kroger]
            if chain != "kroger":
                start_container() >> insertRun() >> scrapeData() >> updateRun(pipeline_action="transform", push=True)  >> transformData() >> updateRun(pipeline_action="archive", push=True) >> archiveData() >> docker_cp_bash >> updateRun(push=False)>> stopContainer() >> send_email
            else:
                docker_cp_venv_files = BashOperator(task_id="bash_docker_cp_venv_files", bash_command=f"docker cp {f'scraper_{chain}_{target_data}'}:/app/tmp/collections /tmp/archive/.venv_files")
                start_container() >> insertRun() >> scrapeData() >> updateRun(pipeline_action="transform", push=True)  >> docker_cp_venv_files >> transformDataVenv() >> updateRun(pipeline_action="archive", push=True) >> archiveData() >> docker_cp_bash >> updateRun(push=False)>> stopContainer() >> send_email
                
            # [END main_flow_non_kroger]

        globals()[dag_id] = dynamic_generated_dag()