import logging
import json
import uuid
import socket
from django.conf import settings
from .models import AcquisitionTask

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Server-side manager for Remote Forensic Agents.
    Handles communication, command dispatch, and data intake.
    """
    
    def __init__(self):
        self.active_agents = {}

    def register_agent(self, agent_data):
        """
        Registers a new agent that calls home.
        """
        agent_id = str(uuid.uuid4())
        self.active_agents[agent_id] = {
            'ip': agent_data.get('ip'),
            'hostname': agent_data.get('hostname'),
            'os': agent_data.get('os'),
            'last_seen': timezone.now()
        }
        logger.info(f"Agent registered: {agent_id} ({agent_data.get('hostname')})")
        return agent_id

    def dispatch_command(self, agent_id, command, params=None):
        """
        Queues a command for the specific agent.
        """
        if agent_id not in self.active_agents:
            raise ValueError(f"Agent {agent_id} not connected")
            
        # simulating sending command
        logger.info(f"Dispatching {command} to {agent_id}")
        return True

    def receive_data_stream(self, agent_id, file_handle):
        """
        Handles incoming data stream from an agent (e.g. memory dump being uploaded).
        """
        pass
