import logging
import time
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    config.load_incluster_config()
except config.ConfigException:
    logger.error("Error fetching kube config file.")

batch_v1 = client.BatchV1Api()