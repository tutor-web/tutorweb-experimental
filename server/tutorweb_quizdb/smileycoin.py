import base64
import codecs
import json
import random
import string
import urllib.request

CONFIG = dict(
    rpc_host='127.0.0.1',
    rpc_port=14242,
    rpc_user='smileycoinrpc',
    rpc_pass='',
    default_account='',
    wallet_passphrase='',
)


def configure(settings, prefix=''):
    for (k, v) in settings.items():
        if prefix:
            if not k.startswith(prefix):
                continue
            k = k.replace(prefix, '')
        if k not in CONFIG:
            raise ValueError("Unknown setting (%s)%s" % (prefix, k))
        CONFIG[k] = v
    return CONFIG


def getBlockCount():
    return callMethod('getblockcount')


def sendTransaction(walletId, coinOwed):
    """Send coinOwed in milli-SMLY to walletId, return tx id if worked"""
    if walletId.startswith('$$UNITTEST'):
        # Unit test wallets don't do anything
        return 'UNITTESTTX:%s:%d' % (walletId, coinOwed)

    if CONFIG['wallet_passphrase']:
        callMethod('walletpassphrase', CONFIG['wallet_passphrase'], 2)
    return callMethod(
        'sendtoaddress',
        walletId,
        float(coinOwed) / 1000,
        "Award from tutorweb",
    )


def getAddress(account=None):
    """
    Fetch a new valid address for the given account, or ''.
    Example return value: u'BFg2HT3r3t9Qf3x931y3EX3Z9333i3TC3m'
    """
    return callMethod(
        'getnewaddress',
        account or CONFIG['default_account'],
    )


def getTransaction(txid):
    """
    Return JSON structure describing given transaction
    Example return value: {
        u'amount': 10000000.0,
        u'blockhash': u'8f2726234290803298409280965a8ff7139789f1ff12f6dd803da08608fc56ea',
        u'blockindex': 1,
        u'blocktime': 1482342386,
        u'confirmations': 15,
        u'details': [{u'account': u'klsdfjlkscount',
                      u'address': u'BL5234902834093284092834098xPk19sb',
                      u'amount': 10000000.0,
                      u'category': u'receive'}],
        u'normtxid': u'eb6cb5019023840982309820398409238409238409328498ccfbbec3c05ca58b',
        u'time': 1482342346,
        u'timereceived': 1234234336,
        u'txid': u'e590093856092348092387092384092830948230948209384092384f888f887c'
    }
    """
    return callMethod(
        'gettransaction',
        txid,
    )


def callMethod(method, *params):
    """Call any JSON-RPC method"""
    def base64_enc(auth):
        """
        Jump through python3 hoops to encode base64 string
        """
        return base64.encodebytes(auth.encode('ascii')).decode('ascii').replace('\n', '')

    callId = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    request = urllib.request.Request('http://%s:%s' % (
        CONFIG['rpc_host'],
        CONFIG['rpc_port'],
    ), json.dumps(dict(
        jsonrpc="1.0",
        id=callId,
        method=method,
        params=params,
    )).encode('utf8'), {
        "Authorization": "Basic %s" % base64_enc('%s:%s' % (CONFIG['rpc_user'], CONFIG['rpc_pass'])),
        "Content-Type": "application/json",
    })

    # Do the request, parse response
    try:
        response = urllib.request.urlopen(request)
        out = json.load(codecs.getreader('utf8')(response))
    except urllib.request.HTTPError as e:
        try:
            out = json.load(codecs.getreader('utf8')(e))
            if not out['error']:
                out['error'] = dict(message='', code=e.code)
        except ValueError:
            out = dict(id=callId, error=dict(
                message=" ".join([e.msg, e.read().decode('utf8')]),
                code=e.code,
            ))

    if out['id'] != callId:
        raise ValueError("Response ID %s doesn't match %s" % (out['id'], callId))

    if out['error'] is None:
        return out['result']

    if out['error']['message'] == "Invalid Smileycoin address":
        raise ValueError(out['error']['message'])

    raise RuntimeError("%s (%d)" % (out['error']['message'], out['error']['code']))
