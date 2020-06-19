import unittest
import unittest.mock

from .requires_postgresql import RequiresPostgresql
from .requires_pyramid import RequiresPyramid

from tutorweb_quizdb.lti import TwRequestValidator, view_tool_config


# NB: We RequiresPyramid to make sure DBSession is set up
class TwRequestValidatorTest(RequiresPyramid, RequiresPostgresql, unittest.TestCase):
    def test_validate_timestamp_and_nonce(self):
        def vtan(cur_time, client_key, timestamp, nonce,
                 request_token=None, access_token=None):
            with unittest.mock.patch('time.time') as mock_time:
                mock_time.return_value = cur_time
                return TwRequestValidator(dict(k1="secret1", k2="secret2")).validate_timestamp_and_nonce(
                    client_key=client_key,
                    timestamp=timestamp,
                    nonce=nonce,
                    request=None,
                    request_token=request_token,
                    access_token=access_token,
                )

        # client_key/nonce/token combos can only be used once
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', 'token1'), True)
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', 'token1'), False)
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', 'token2'), True)
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', 'token2'), False)
        self.assertEqual(vtan(1000, 'k2', 1000, 'nonce1', 'token2'), True)
        self.assertEqual(vtan(1000, 'k2', 1000, 'nonce1', 'token2'), False)
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', access_token='token2'), False)

        # Nonces can't be used if they're too old
        self.assertEqual(vtan(9000, 'k1', 1000, 'nonce2', 'token20'), False)

        # Could in theory wind back time and re-use one (shows we're tidying up)
        self.assertEqual(vtan(1000, 'k1', 1000, 'nonce1', 'token30'), True)
        self.assertEqual(vtan(1100, 'k1', 1000, 'nonce1', 'token30'), False)  # Doesn't work
        self.assertEqual(vtan(9000, 'k1', 1000, 'nonce2', 'token32'), False)  # In the future, we tidy up
        self.assertEqual(vtan(1100, 'k1', 1000, 'nonce1', 'token30'), True)  # Now it works

    def test_validate_client_key(self):
        def vck(client_key):
            return TwRequestValidator(dict(k1="secret1", k2="secret2")).validate_client_key(client_key, None)

        self.assertEqual(vck("k1"), True)
        self.assertEqual(vck("k2"), True)
        self.assertEqual(vck("non-existant"), False)
        self.assertEqual(vck(None), False)

    def test_get_client_secret(self):
        def gcs(client_key):
            return TwRequestValidator(dict(k1="secret1", k2="secret2")).get_client_secret(client_key, None)

        self.assertEqual(gcs("k1"), "secret1")
        self.assertEqual(gcs("k2"), "secret2")
        self.assertEqual(gcs("non-existant"), "dummy_secret")
        self.assertEqual(gcs(None), "dummy_secret")

    def test_dummy_secret(self):
        """Will use dummy secret when "validating" invalid keys, so implement it"""
        v = TwRequestValidator(dict(k1="secret1", k2="secret2"))
        self.assertTrue(isinstance(v.dummy_client, str))
        self.assertTrue(isinstance(v.get_client_secret(v.dummy_client, None), str))

        # The dummy key isn't valid
        self.assertFalse(v.validate_client_key(v.dummy_client, None))

        # Can't accidentally add it to the secrets DB
        with self.assertRaises(AssertionError):
            TwRequestValidator({v.dummy_client: "woo"})


class ViewToolConfigTest(RequiresPyramid, unittest.TestCase):
    def test_call(self):
        resp = view_tool_config(self.request())
        self.assertEqual(resp.content_type, 'text/xml')
        self.assertTrue(resp.body.startswith(b'<?xml version="1.0" encoding="UTF-8"?><cartridge_basiclti_link'))
