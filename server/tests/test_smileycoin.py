import base64
import io
import json
import unittest
import urllib.request


from tutorweb_quizdb import smileycoin


class TestSmileyCoin(unittest.TestCase):
    def tearDown(self):
        chooseOpener()

    def test_utTransactions(self):
        """Unit-test transactions do nothing"""
        chooseOpener(NoHTTPHandler)

        self.assertEqual(
            smileycoin.sendTransaction('$$UNITTEST01', 99),
            "UNITTESTTX:$$UNITTEST01:99",
        )

    def test_realTransaction(self):
        """Requests get properly encoded"""
        chooseOpener(MockHTTPHandler)
        global nextResponse

        # Configure with usless settings
        smileycoin.configure(dict(
            rpc_host="moohost",
            rpc_port=900,
            rpc_user="smly",
            rpc_pass="realgoodpassword",
            wallet_passphrase=None,
        ))

        nextResponse = dict(result=1234)
        self.assertEqual(smileycoin.sendTransaction('WaLlEt', 23), 1234)
        self.assertEqual(requests[-1], dict(
            url='http://moohost:900',
            contenttype='application/json',
            auth='smly:realgoodpassword',
            data=dict(
                id=requests[-1]['data']['id'],
                jsonrpc=u'1.0',
                method=u'sendtoaddress',
                params=[u'WaLlEt', 0.023, u'Award from tutorweb'],
            ),
        ))

        # Try another transaction
        nextResponse = dict(result=8421)
        self.assertEqual(smileycoin.sendTransaction('WALL-E', 84), 8421)
        self.assertEqual(requests[-1], dict(
            url='http://moohost:900',
            contenttype='application/json',
            auth='smly:realgoodpassword',
            data=dict(
                id=requests[-1]['data']['id'],
                jsonrpc=u'1.0',
                method=u'sendtoaddress',
                params=[u'WALL-E', 0.084, u'Award from tutorweb'],
            ),
        ))

        # IDs shouldn't match
        for i in range(100):
            self.assertEqual(smileycoin.sendTransaction('WALL-E', 84), 1234)
        self.assertEqual(
            len([r['data']['id'] for r in requests]),
            len(set([r['data']['id'] for r in requests])),
        )

    def test_errorTransaction(self):
        """Test failures fail"""
        chooseOpener(MockHTTPHandler)
        global nextResponse

        # General failure
        nextResponse = dict(error=dict(message="oh noes", code=-42))
        with self.assertRaisesRegexp(RuntimeError, "oh noes \(\-42\)"):
            smileycoin.sendTransaction('WALL-E', 84)

        # Mismatching response ID
        nextResponse = dict(id="camel")
        with self.assertRaisesRegexp(ValueError, "camel"):
            smileycoin.sendTransaction('WALL-E', 84)

        # Invalid address
        nextResponse = dict(error=dict(message="Invalid Smileycoin address", code=-5))
        with self.assertRaisesRegexp(ValueError, "Smileycoin"):
            smileycoin.sendTransaction('WALL-E', 84)

    def test_httpErrors(self):
        """Test failures fail"""
        chooseOpener(MockHTTPHandler)
        global nextResponse

        # General failure
        nextResponse = dict(_code=401, _msg='ERROR', _data="<html><body>401 Unauthorized, innit</body></html>")
        with self.assertRaisesRegexp(RuntimeError, "ERROR.+\(401\)"):
            smileycoin.sendTransaction('WALL-E', 84)

    def test_walletOpening(self):
        """Wallets can be opened first"""
        chooseOpener(MockHTTPHandler)
        global nextResponse

        # Configure with usless settings
        smileycoin.configure(dict(
            rpc_host="moohost",
            rpc_port=900,
            rpc_user="smelly",
            rpc_pass="badpassword",
            wallet_passphrase="letmein",
        ))

        self.assertEqual(smileycoin.sendTransaction('WaLlEt', 23), 1234)
        self.assertEqual(requests[-2], dict(
            url='http://moohost:900',
            contenttype='application/json',
            auth='smelly:badpassword',
            data=dict(
                id=requests[-2]['data']['id'],
                jsonrpc=u'1.0',
                method=u'walletpassphrase',
                params=['letmein', 2],
            ),
        ))
        self.assertEqual(requests[-1], dict(
            url='http://moohost:900',
            contenttype='application/json',
            auth='smelly:badpassword',
            data=dict(
                id=requests[-1]['data']['id'],
                jsonrpc=u'1.0',
                method=u'sendtoaddress',
                params=[u'WaLlEt', 0.023, u'Award from tutorweb'],
            ),
        ))


class NoHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        raise ValueError("I said no HTTP")


requests = []
nextResponse = {}


class MockHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        requests.append(dict(
            url=req.get_full_url(),
            contenttype=req.headers['Content-type'],
            auth=base64.decodestring(req.headers['Authorization'].replace('Basic ', '').encode('utf8')).decode('utf8'),
            data=json.loads(req.data.decode('utf8')),
        ))

        # Sanitise response
        global nextResponse
        if 'id' not in nextResponse:
            nextResponse['id'] = requests[-1]['data']['id']
        if 'error' not in nextResponse:
            nextResponse['error'] = None
        if 'result' not in nextResponse:
            nextResponse['result'] = 1234

        resp = urllib.response.addinfourl(
            io.BytesIO((nextResponse['_data'] if '_data' in nextResponse else json.dumps(nextResponse)).encode('utf8')),
            "Message of some form",
            req.get_full_url(),
        )
        resp.code = nextResponse['_code'] if '_code' in nextResponse else 200
        resp.msg = nextResponse['_msg'] if '_msg' in nextResponse else "OK"
        nextResponse = dict()
        return resp


def chooseOpener(klass=None):
    if klass is None:
        opener = urllib.request.build_opener()
    else:
        opener = urllib.request.build_opener(klass)
    urllib.request.install_opener(opener)
