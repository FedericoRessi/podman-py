import unittest

import requests_mock

from podman import PodmanClient
from podman.domain.pods import Pod
from podman.domain.pods_manager import PodsManager
from podman.errors import NotFound

FIRST_POD = {
    "ID": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
    "Name": "blog-nginx",
}
SECOND_POD = {
    "ID": "c847d00ed0474835a2e246f00e90346fe98d388f98064f4494953c5fb921b8bc",
    "Name": "podman",
}


class PodsManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url="http+unix://localhost:9999")

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.pods
        self.assertIsInstance(manager, PodsManager)

    @requests_mock.Mocker()
    def test_create(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods/create",
            json={"Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"},
        )
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )

        actual = self.client.pods.create(name="database")
        self.assertIsInstance(actual, Pod)

        self.assertTrue(adapter.called_once)
        self.assertDictEqual(adapter.last_request.json(), {"name": "database"})

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            "http+unix://localhost:9999/v3.0.0/libpod/pods"
            "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
            json=FIRST_POD,
        )

        actual = self.client.pods.get(
            "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )
        self.assertEqual(
            actual.id, "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )

        @requests_mock.Mocker()
        def test_get404(self, mock):
            mock.get(
                "http+unix://localhost:9999/v3.0.0/libpod/pods"
                "/c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8/json",
                status_code=404,
                json={
                    "cause": "no such pod",
                    "message": "no pod with name or ID "
                    "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
                    " found: no such pod",
                    "response": 404,
                },
            )

            with self.assertRaises(NotFound):
                self.client.pods.get(
                    "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
                )

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get("http+unix://localhost:9999/v3.0.0/libpod/pods/json", json=[FIRST_POD, SECOND_POD])

        actual = self.client.pods.list()

        self.assertEqual(
            actual[0].id, "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8"
        )
        self.assertEqual(
            actual[1].id, "c847d00ed0474835a2e246f00e90346fe98d388f98064f4494953c5fb921b8bc"
        )

    @requests_mock.Mocker()
    def test_prune(self, mock):
        adapter = mock.post(
            "http+unix://localhost:9999/v3.0.0/libpod/pods/prune",
            json=[
                {
                    "Err": None,
                    "Id": "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
                },
                {
                    "Err": None,
                    "Id": "c847d00ed0474835a2e246f00e90346fe98d388f98064f4494953c5fb921b8bc",
                },
            ],
        )

        actual = self.client.pods.prune()
        self.assertTrue(adapter.called_once)
        self.assertListEqual(
            actual["PodsDeleted"],
            [
                "c8b9f5b17dc1406194010c752fc6dcb330192032e27648db9b14060447ecf3b8",
                "c847d00ed0474835a2e246f00e90346fe98d388f98064f4494953c5fb921b8bc",
            ],
        )
        self.assertEqual(actual["SpaceReclaimed"], 0)


if __name__ == '__main__':
    unittest.main()
