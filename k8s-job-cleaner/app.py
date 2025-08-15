import logging
import time
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    config.load_incluster_config()
except config.ConfigException:
    logger.error("Error fetching kube config file.")

batch_v1 = client.BatchV1Api()

namespace = os.getenv('namespace')
logger.info(f"Monitoring Jobs in namespace: {namespace}")


def is_job_completed(job):
    conditions = job.status.conditions or []
    for condition in conditions:
        if condition.type == 'Complete' and condition.status == 'True':
            return True
    return False

def delete_job(namespace, name):
    try:
        batch_v1.delete_namespaced_job(
            name=name,
            namespace=namespace,
            propagation_policy='Background'
        )
        logger.info(f"Successfully deleted Job {namespace}/{name}")
    except ApiException as e:
        logger.error(f"Failed to delete Job {namespace}/{name}: {e}")

def watch_jobs():
    w = watch.Watch()
    while True:
        try:
            logger.info(f"Starting watch for Jobs in namespace {namespace}")
            for event in w.stream(batch_v1.list_namespaced_job, namespace=namespace, timeout_seconds=60):
                job = event['object']
                name = job.metadata.name

                if not name:
                    logger.warning(f"Skipping Job with missing name: {event}")
                    continue

                if is_job_completed(job):
                    logger.info(f"Detected completed Job {namespace}/{name}")
                    delete_job(name)

        except ApiException as e:
            logger.error(f"API error during watch: {e}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(5)
        finally:
            w.stop()

if __name__ == '__main__':
    try:
        watch_jobs()
    except KeyboardInterrupt:
        logger.info("Shutting down Job cleanup agent")