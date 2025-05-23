# For testing rate-limiting middleware
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def load_test(self):
        self.client.get("/")

