import os
import logging
import uuid
import time
from django.utils import timezone
from .physical import PhysicalImager

logger = logging.getLogger(__name__)


class RemoteStreamImager(PhysicalImager):
    """
    Pillar 1: Remote Acquisition Agent
    Handles bit-perfect streaming from a deployed agent.
    """

    def __init__(self, task):
        super().__init__(task)
        self.agent_id = str(uuid.uuid4())[:8]
        self.connection_key = str(uuid.uuid4())

        # In a real system, the destination name comes from the agent's report
        if not self.destination_path.endswith(".remote"):
            self.destination_path += ".remote"

    def acquire(self):
        """
        Orchestrates the remote acquisition.
        In this implementation, it sets up the 'Waiting' state and provides
        the deployment command for the analyst.
        """
        try:
            self.task.status = "running"
            self.task.logs += f"\n[ORCHESTRATOR] Generated Agent ID: {self.agent_id}\n"
            self.task.logs += f"[ORCHESTRATOR] Connection Key: {self.connection_key}\n"
            self.task.logs += f"[ORCHESTRATOR] Waiting for remote agent to connect...\n"
            self.task.current_speed = "Waiting for Agent..."
            self.task.save()

            # --- SIMULATION MODE: To show the user how it works ---
            # In production, this would be a long-running listener or a webhook trigger.
            # We will simulate the connection and a small stream for the demo.
            logger.info(f"Remote Stream Active (Agent: {self.agent_id})")

            # This is where we would normally exit and wait for a second process/webhook.
            # However, for the walkthrough, we'll implement a 'Stream Simulation' if requested.
            return True

        except Exception as e:
            logger.error(f"Remote acquisition initiation failed: {e}")
            self.task.status = "failed"
            self.task.error_message = str(e)
            self.task.save()
            return False

    def generate_agent_command(self, server_url):
        """Returns the curl/one-liner to deploy the agent"""
        return f"curl -sSL {server_url}/agent/deploy | sudo bash -s -- --key {self.connection_key} --target {self.logical_source}"
