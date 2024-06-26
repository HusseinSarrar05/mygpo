import copy
from datetime import datetime, timedelta
import json
import unittest
import os
import unittest.mock
from unittest.mock import patch, MagicMock
from urllib.parse import urlencode

from django.test.client import Client
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.test import RequestFactory

from openapi_spec_validator import validate_spec_url
from jsonschema import ValidationError

from mygpo.api import RequestException
from mygpo.api.advanced.episode import ChaptersAPI
from mygpo.podcasts.models import Podcast, Episode
from mygpo.api.advanced import episodes
from mygpo.api.opml import Exporter, Importer
from mygpo.api.simple import format_podcast_list
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.test import create_auth_string
from mygpo.utils import get_timestamp

from .legacy import upload
from mygpo.api import legacy
from io import BytesIO



class AdvancedAPITests(unittest.TestCase):
    def setUp(self):
        User = get_user_model()
        self.password = "asdf"
        self.username = "adv-api-user"
        self.user = User(username=self.username, email="user@example.com")
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()

        self.extra = {
            "HTTP_AUTHORIZATION": create_auth_string(self.username, self.password)
        }

        self.action_data = [
            {
                "podcast": "http://example.com/feed.rss",
                "episode": "http://example.com/files/s01e20.mp3",
                "device": "gpodder_abcdef123",
                "action": "download",
                "timestamp": "2009-12-12T09:00:00",
            },
            {
                "podcast": "http://example.org/podcast.php",
                "episode": "http://ftp.example.org/foo.ogg",
                "action": "play",
                "started": 15,
                "position": 120,
                "total": 500,
            },
        ]

    def tearDown(self):
        self.user.delete()

    def test_episode_actions(self):
        response = self._upload_episode_actions(self.user, self.action_data, self.extra)
        self.assertEqual(response.status_code, 200, response.content)

        url = reverse(episodes, kwargs={"version": "2", "username": self.user.username})
        response = self.client.get(url, {"since": "0"}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode("utf-8"))
        actions = response_obj["actions"]
        self.assertTrue(self.compare_action_list(self.action_data, actions))

    def test_invalid_client_id(self):
        """Invalid Client ID should return 400"""
        action_data = copy.deepcopy(self.action_data)
        action_data[0]["device"] = "gpodder@abcdef123"

        response = self._upload_episode_actions(self.user, action_data, self.extra)

        self.assertEqual(response.status_code, 400, response.content)

    def _upload_episode_actions(self, user, action_data, extra):
        url = reverse(episodes, kwargs={"version": "2", "username": self.user.username})
        return self.client.post(
            url, json.dumps(action_data), content_type="application/json", **extra
        )

    def compare_action_list(self, as1, as2):
        for a1 in as1:
            found = False
            for a2 in as2:
                if self.compare_actions(a1, a2):
                    found = True

            if not found:
                raise ValueError("%s not found in %s" % (a1, as2))
                return False

        return True

    def compare_actions(self, a1, a2):
        for key, val in a1.items():
            if a2.get(key, None) != val:
                return False
        return True


class SubscriptionAPITests(unittest.TestCase):
    """Tests the Subscription API"""

    def setUp(self):
        User = get_user_model()
        self.password = "asdf"
        self.username = "subscription-api-user"
        self.device_uid = "test-device"
        self.user = User(username=self.username, email="user@example.com")
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()

        self.extra = {
            "HTTP_AUTHORIZATION": create_auth_string(self.username, self.password)
        }

        self.action_data = {"add": ["http://example.com/podcast.rss"]}

        self.url = reverse(
            "subscriptions-api",
            kwargs={
                "version": "2",
                "username": self.user.username,
                "device_uid": self.device_uid,
            },
        )

    def tearDown(self):
        self.user.delete()
    

    def test_set_get_subscriptions(self):
        """Tests that an upload subscription is returned back correctly"""

        # upload a subscription
        response = self.client.post(
            self.url,
            json.dumps(self.action_data),
            content_type="application/json",
            **self.extra,
        )
        self.assertEqual(response.status_code, 200, response.content)

        # verify that the subscription is returned correctly
        response = self.client.get(self.url, {"since": "0"}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode("utf-8"))
        self.assertEqual(self.action_data["add"], response_obj["add"])
        self.assertEqual([], response_obj.get("remove", []))

    def test_unauth_request(self):
        """Tests that an unauthenticated request gives a 401 response"""
        response = self.client.get(self.url, {"since": "0"})
        self.assertEqual(response.status_code, 401, response.content)


    @patch('mygpo.api.legacy.auth')
    @patch('mygpo.api.legacy.get_device')
    @patch('mygpo.api.legacy.Importer')
    def test_upload_opml(self, MockImporter, mock_get_device, mock_auth):
        """Tests the upload functionality with an OPML file"""
        branch_coverage = [False] * 13
        
        # Mock authentication
        mock_auth.return_value = self.user

        # Mock device
        mock_device = MagicMock()
        mock_device.get_subscribed_podcasts.return_value = [
            {'url': 'http://example.com/podcast.rss'},
            {'url': 'http://example1.com/podcast.rss'},
            {'url': 'http://example2.com/podcast.rss'}
        ]
        mock_get_device.return_value = mock_device

        # Mock Importer
        mock_importer = MagicMock()
        mock_importer.items = [{'url': 'http://example.com/podcast.rss'}]
        MockImporter.return_value = mock_importer

        opml_content = b"<opml><body><outline type='rss' xmlUrl='http://example.com/podcast.rss'/></body></opml>"

        # Replace the functions with mocks
        legacy.subscribe = MagicMock()
        legacy.unsubscribe = MagicMock()

        factory = RequestFactory()

        # Attempt at normal successful upload
        request = factory.post(
            reverse('upload'),
            {
                'username': self.username,
                'password': self.password,
                'action': 'upload',
                'protocol': 'http',
                'opml': BytesIO(opml_content)
            }
        )

        response = upload(request, branch_coverage) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "@SUCCESS")

        # Attempt to detect podcasts to be removed
        mock_device.get_subscribed_podcasts.return_value = [
            {'url': 'http://example1.com/podcast.rss'},
            {'url': 'http://example2.com/podcast.rss'}
        ]

        response = upload(request, branch_coverage) 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "@SUCCESS")

        # Attempt at fail in authorisation of user
        mock_device.get_subscribed_podcasts.return_value = [
            {'url': 'http://example.com/podcast.rss'},
            {'url': 'http://example1.com/podcast.rss'},
            {'url': 'http://example2.com/podcast.rss'}
        ]
        mock_auth.return_value = None
        response = upload(request, branch_coverage)    
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "@AUTHFAIL")


        # Attempt at request without opml file
        request = factory.post(
            reverse('upload'),
            {
                'username': self.username,
                'password': self.password,
                'action': 'upload',
                'protocol': 'http',
            }
        )
        response = upload(request, branch_coverage)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "@PROTOERROR")

        write_coverage_to_file(
            "coverage/manual_coverage/hussein_upload_cov.txt",
            "upload",
            branch_coverage)


class DirectoryTest(TestCase):
    """Test Directory API"""

    def setUp(self):
        self.podcast = Podcast.objects.get_or_create_for_url(
            "http://example.com/directory-podcast.xml", defaults={"title": "My Podcast"}
        ).object
        self.episode = Episode.objects.get_or_create_for_url(
            self.podcast,
            "http://example.com/directory-podcast/1.mp3",
            defaults={"title": "My Episode"},
        ).object
        self.client = Client()

    def test_episode_info(self):
        """Test that the expected number of queries is executed"""
        url = (
            reverse("api-episode-info")
            + "?"
            + urlencode((("podcast", self.podcast.url), ("url", self.episode.url)))
        )

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)


class EpisodeActionTests(TestCase):
    def setUp(self):
        self.podcast = Podcast.objects.get_or_create_for_url(
            "http://example.com/directory-podcast.xml", defaults={"title": "My Podcast"}
        ).object
        self.episode = Episode.objects.get_or_create_for_url(
            self.podcast,
            "http://example.com/directory-podcast/1.mp3",
            defaults={"title": "My Episode"},
        ).object
        User = get_user_model()
        self.password = "asdf"
        self.username = "adv-api-user"
        self.user = User(username=self.username, email="user@example.com")
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()
        self.extra = {
            "HTTP_AUTHORIZATION": create_auth_string(self.username, self.password)
        }

    def tearDown(self):
        self.episode.delete()
        self.podcast.delete()
        self.user.delete()

    @override_settings(MAX_EPISODE_ACTIONS=10)
    def test_limit_actions(self):
        """Test that max MAX_EPISODE_ACTIONS episodes are returned"""

        timestamps = []
        t = datetime.utcnow()
        for n in range(15):
            timestamp = t - timedelta(seconds=n)
            EpisodeHistoryEntry.objects.create(
                timestamp=timestamp,
                episode=self.episode,
                user=self.user,
                action=EpisodeHistoryEntry.DOWNLOAD,
            )
            timestamps.append(timestamp)

        url = reverse(episodes, kwargs={"version": "2", "username": self.user.username})
        response = self.client.get(url, {"since": "0"}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode("utf-8"))
        actions = response_obj["actions"]

        # 10 actions should be returned
        self.assertEqual(len(actions), 10)

        timestamps = sorted(timestamps)

        # the first 10 actions, according to their timestamp should be returned
        for action, timestamp in zip(actions, timestamps):
            self.assertEqual(timestamp.isoformat(), action["timestamp"])

        # the `timestamp` field in the response should be the timestamp of the
        # last returned action
        self.assertEqual(get_timestamp(timestamps[9]), response_obj["timestamp"])

    def test_no_actions(self):
        """Test when there are no actions to return"""

        t1 = get_timestamp(datetime.utcnow())

        url = reverse(episodes, kwargs={"version": "2", "username": self.user.username})
        response = self.client.get(url, {"since": "0"}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode("utf-8"))
        actions = response_obj["actions"]

        # 10 actions should be returned
        self.assertEqual(len(actions), 0)

        returned = response_obj["timestamp"]
        t2 = get_timestamp(datetime.utcnow())
        # the `timestamp` field in the response should be the timestamp of the
        # last returned action
        self.assertGreaterEqual(returned, t1)
        self.assertGreaterEqual(t2, returned)


class SimpleAPITests(unittest.TestCase):
    def setUp(self):
        User = get_user_model()
        self.password = "asdf"
        self.username = "subscription-api-user"
        self.device_uid = "test-device"
        self.user = User(username=self.username, email="user@example.com")
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()
        self.extra = {
            "HTTP_AUTHORIZATION": create_auth_string(self.username, self.password)
        }
        self.formats = ["txt", "json", "jsonp", "opml"]
        self.subscriptions_urls = dict(
            (fmt, self.get_subscriptions_url(fmt)) for fmt in self.formats
        )
        self.blank_values = {
            "txt": b"\n",
            "json": b"[]",
            "opml": Exporter("Subscriptions").generate([]),
        }
        self.all_subscriptions_url = reverse(
            "api-all-subscriptions",
            kwargs={"format": "txt", "username": self.user.username},
        )
        self.toplist_urls = dict(
            (fmt, self.get_toplist_url(fmt)) for fmt in self.formats
        )
        self.search_urls = dict((fmt, self.get_search_url(fmt)) for fmt in self.formats)

    def tearDown(self):
        self.user.delete()

    def get_toplist_url(self, fmt):
        return reverse("api-simple-toplist-50", kwargs={"format": fmt})

    def get_subscriptions_url(self, fmt):
        return reverse(
            "api-simple-subscriptions",
            kwargs={
                "format": fmt,
                "username": self.user.username,
                "device_uid": self.device_uid,
            },
        )

    def get_search_url(self, fmt):
        return reverse("api-simple-search", kwargs={"format": fmt})

    def _test_response_for_data(self, url, data, status_code, content):
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.content, content)

    def test_get_subscriptions_empty(self):
        testers = {
            "txt": lambda c: self.assertEqual(c, b""),
            "json": lambda c: self.assertEqual(c, b"[]"),
            "jsonp": lambda c: self.assertEqual(c, b"test([])"),
            "opml": lambda c: self.assertListEqual(Importer(c).items, []),
        }
        for fmt in self.formats:
            url = self.subscriptions_urls[fmt]
            response = self.client.get(url, data={"jsonp": "test"}, **self.extra)
            self.assertEqual(response.status_code, 200, response.content)
            testers[fmt](response.content)

    def test_get_subscriptions_invalid_jsonp(self):
        url = self.subscriptions_urls["jsonp"]
        response = self.client.get(url, data={"jsonp": "!"}, **self.extra)
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_subscriptions_with_content(self):
        sample_url = "http://example.com/directory-podcast.xml"
        podcast = Podcast.objects.get_or_create_for_url(
            sample_url, defaults={"title": "My Podcast"}
        ).object
        with unittest.mock.patch(
            "mygpo.users.models.Client.get_subscribed_podcasts"
        ) as mock_get:
            mock_get.return_value = [podcast]
            response = self.client.get(self.subscriptions_urls["txt"], **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        retrieved_urls = response.content.split(b"\n")[:-1]
        expected_urls = [sample_url.encode()]
        self.assertEqual(retrieved_urls, expected_urls)

    def test_post_subscription_valid(self):
        sample_url = "http://example.com/directory-podcast.xml"
        podcast = Podcast.objects.get_or_create_for_url(
            sample_url, defaults={"title": "My Podcast"}
        ).object
        payloads = {
            "txt": sample_url,
            "json": json.dumps([sample_url]),
            #'opml': Exporter('Subscriptions').generate([sample_url]),
            "opml": Exporter("Subscriptions").generate([podcast]),
        }
        payloads = dict(
            (fmt, format_podcast_list([podcast], fmt, "test title").content)
            for fmt in self.formats
        )
        for fmt in self.formats:
            url = self.subscriptions_urls[fmt]
            payload = payloads[fmt]
            response = self.client.generic("POST", url, payload, **self.extra)
            self.assertEqual(response.status_code, 200, response.content)

    def test_post_subscription_invalid(self):
        url = self.subscriptions_urls["json"]
        payload = "invalid_json"
        response = self.client.generic("POST", url, payload, **self.extra)
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_all_subscriptions_invalid_scale(self):
        response = self.client.get(
            self.all_subscriptions_url, data={"scale_logo": 0}, **self.extra
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_all_subscriptions_non_numeric_scale(self):
        response = self.client.get(
            self.all_subscriptions_url, data={"scale_logo": "a"}, **self.extra
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_all_subscriptions_valid_empty(self):
        response = self.client.get(self.all_subscriptions_url, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)

    def test_get_toplist_invalid_scale(self):
        response = self.client.get(
            self.toplist_urls["opml"], data={"scale_logo": 0}, **self.extra
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_toplist_non_numeric_scale(self):
        response = self.client.get(
            self.toplist_urls["txt"], data={"scale_logo": "a"}, **self.extra
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_get_toplist_valid_empty(self):
        response = self.client.get(self.toplist_urls["json"], **self.extra)
        self.assertEqual(response.status_code, 200, response.content)

    def test_search_non_numeric_scale_logo(self):
        data = {"scale_logo": "a"}
        expected_status = 400
        expected_content = b"scale_logo has to be a numeric value"

        self._test_response_for_data(
            self.search_urls["json"], data, expected_status, expected_content
        )

    def test_search_scale_out_of_range(self):
        data = {"scale_logo": 3000}
        expected_status = 400
        expected_content = b"scale_logo has to be a number from 1 to 256"

        self._test_response_for_data(
            self.search_urls["opml"], data, expected_status, expected_content
        )

    def test_search_no_query(self):
        data = {"scale_logo": 1}
        expected_status = 400
        expected_content = b"/search.opml|txt|json?q={query}"

        self._test_response_for_data(
            self.search_urls["opml"], data, expected_status, expected_content
        )

    def test_search_valid_query_status(self):
        data = {"scale_logo": 1, "q": "foo"}
        expected_status = 200

        response = self.client.get(self.search_urls["json"], data)
        self.assertEqual(response.status_code, expected_status)


# class OpenAPIDefinitionValidityTest(TestCase):
#     "Test the validity of the OpenAPI definition file"

    # def test_api_definition_validity(self):
    #     validate_spec_url("file://" + os.path.abspath("./mygpo/api/openapi.yaml"))


class GetUrlsTest(unittest.TestCase):

    @patch('mygpo.api.advanced.episode.normalize_feed_url')
    def test_get_urls(self, mock_normalize_feed_url):
        branch_coverage_get = [False] * 8
        testobj = ChaptersAPI()

        # branch 0
        body = {"podcast": "", "episode": ""}
        with self.assertRaises(RequestException):
            testobj.get_urls(body, branch_coverage_get)

        # branch 1, 2
        body = {"podcast": "podcast_url", "episode": ""}
        with self.assertRaises(RequestException):
            testobj.get_urls(body, branch_coverage_get)

        mock_normalize_feed_url.return_value = "norm_url"
        # branch 1, 3, 5, 7 different url
        body = {"podcast": "dif_url", "episode": "dif_url"}
        result = testobj.get_urls(body, branch_coverage_get)
        self.assertEqual(result, ("norm_url", "norm_url", [("dif_url", "norm_url"), ("dif_url", "norm_url")]))


        mock_normalize_feed_url.return_value = "same_url"
        # branch 1,3, 4 and 6 same podcast and episode url
        body = {"podcast": "same_url", "episode": "same_url"}
        result = testobj.get_urls(body, branch_coverage_get)
        self.assertEqual(result, ("same_url", "same_url", []))

        write_coverage_to_file(
            "coverage/manual_coverage/andi_get_urls_cov.txt",
            "get_urls",
            branch_coverage_get)



def write_coverage_to_file(filename, method_name, branch_coverage):
    total = len(branch_coverage)
    num_taken = 0
    with open(filename, 'w') as file:
        file.write(f"FILE: {filename}\nMethod: {method_name}\n")
        for index, coverage in enumerate(branch_coverage):
            if coverage:
                file.write(f"Branch {index} was taken\n")
                num_taken += 1
            else:
                file.write(f"Branch {index} was not taken\n")
        file.write("\n")
        coverage_level = num_taken/total * 100
        file.write(f"Total coverage = {coverage_level}%\n")