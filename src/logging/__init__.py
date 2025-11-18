"""
Logging Configuration Module

Provides centralized logging configuration for the Ontology MCP Plugin.
"""

import os
import logging
import logging.config
import yaml

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Load logging configuration
config_path = os.path.join(os.path.dirname(__file__), 'logger_conf.yml')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Create logger for the module
logger = logging.getLogger('ontology_mcp')
