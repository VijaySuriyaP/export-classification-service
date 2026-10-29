"""Locust scenario measuring submit-to-terminal-result latency, not just POST time."""
from __future__ import annotations

import time
import uuid

from locust import HttpUser, between, task


class ClassificationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        self.client_id = f"locust-{uuid.uuid4().hex}"

    @task
    def submit_and_poll_to_completion(self) -> None:
        payload = {
            "client_request_id": str(uuid.uuid4()),
            "product_description": "Stainless steel vacuum flask for carrying hot drinks",
            "materials": ["stainless_steel"],
            "destination_country": "US",
            "client_id": self.client_id,
        }
        start = time.perf_counter()
        with self.client.post("/v1/classify", json=payload, name="POST /v1/classify", catch_response=True) as response:
            if response.status_code != 202:
                response.failure(f"submit returned {response.status_code}")
                return
            run_id = response.json().get("run_id")
        for _ in range(180):
            poll = self.client.get(f"/v1/runs/{run_id}", name="GET /v1/runs/[id]")
            if poll.status_code != 200:
                continue
            status = poll.json().get("status")
            if status in {"completed", "failed_escalated"}:
                elapsed = time.perf_counter() - start
                # A separate custom request event makes end-to-end latency visible in Locust stats.
                self.environment.events.request.fire(request_type="E2E", name="submit-to-terminal-result",
                    response_time=elapsed * 1000, response_length=len(poll.content), exception=None, context={})
                return
            time.sleep(0.25)
        self.environment.events.request.fire(request_type="E2E", name="submit-to-terminal-result",
            response_time=(time.perf_counter() - start) * 1000, response_length=0,
            exception=TimeoutError("terminal run state not observed within polling window"), context={})
