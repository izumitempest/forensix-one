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
    Handles real-time streaming from a deployed agent.
    """

    def __init__(self, task):
        super().__init__(task)
        self.agent_id = str(task.id)[:8]
        self.connection_key = str(task.id)

        # Ensure the destination path has the correct extension
        if not self.destination_path.endswith(".remote"):
            self.destination_path += ".remote"

    def acquire(self):
        """
        Orchestrates the remote acquisition.
        Sets the state to 'Running' (Waiting for Agent) and polls for the stream to complete.
        """
        try:
            self.task.status = "running"
            self.task.save()

            self._validate_paths()

            self.task.logs += f"\n[ORCHESTRATOR] Generated Agent ID: {self.agent_id}\n"
            self.task.logs += f"[ORCHESTRATOR] Connection Key: {self.connection_key}\n"
            self.task.logs += f"[ORCHESTRATOR] Waiting for remote agent to connect...\n"
            self.task.current_speed = "Waiting for Agent..."
            self.task.save()

            logger.info(f"Remote Stream Orchestrator Active (Agent: {self.agent_id})")

            # --- REAL-TIME INGESTION ---
            # The server will wait for the AgentStreamView to finalize the task.
            # We poll with a 1 hour timeout.
            timeout = 3600
            start_time = time.time()

            while time.time() - start_time < timeout:
                self.task.refresh_from_db()

                if self.task.status == "completed":
                    logger.info(
                        f"Remote stream finalized successfully for {self.agent_id}"
                    )
                    # Consolidate finalization in the orchestrator
                    self._finalize_task()
                    return True

                if self.task.status == "failed":
                    logger.error(
                        f"Remote stream ingestion failed: {self.task.error_message}"
                    )
                    return False

                # If data started flowing, update speed display (done by AgentStreamView)
                # We just sleep to keep the worker task alive
                time.sleep(2)

            self.task.status = "failed"
            self.task.error_message = (
                "Remote acquisition timed out (No agent connection received)."
            )
            self.task.save()
            return False

        except Exception as e:
            logger.error(f"Remote acquisition initiation failed: {e}")
            self.task.status = "failed"
            self.task.error_message = str(e)
            self.task.save()
            return False

    def generate_agent_command(self, server_url):
        """Returns the curl/one-liner to deploy the agent"""
        return f"curl -sSL {server_url}/agent/deploy | bash -s -- --key {self.connection_key}"
