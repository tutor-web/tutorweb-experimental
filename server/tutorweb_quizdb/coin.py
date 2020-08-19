import datetime

from pyramid.httpexceptions import HTTPForbidden
from pyramid.response import Response
from sqlalchemy.sql import func

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.timestamp import datetime_to_timestamp
from tutorweb_quizdb import smileycoin
from tutorweb_quizdb.student import get_current_student

MAX_STUDENT_HOURLY_AWARD = 7 * 10**6 * 1000  # 7 million milliSMLY
MAX_DAILY_AWARD = 15 * 10**6 * 1000  # 15 million milliSMLY


def view_totalcoin(request):
    """Show approximate number of coins"""
    out = (smileycoin.getBlockCount() - 1000) * 10000 + 24000000000
    return Response(str(out), status=200, content_type="text/plain")


def view_verifystudent(request):
    """Verify a student via. LTI"""
    import hashlib
    from .lti import PyramidToolProvider, request_validator

    # Find out who they are via. LTI
    tool_provider = PyramidToolProvider.from_pyramid_request(request=request)
    if not tool_provider.is_valid_request(request_validator):
        raise HTTPForbidden("Not a valid OAuth request")
    user_identity = request.params.get("user_id", "")
    if "custom_canvas_user_login_id" in request.params:
        user_identity += ":%s" % request.params["custom_canvas_user_login_id"]
    message = hashlib.sha256()
    message.update((user_identity + "?" + request.query_string).encode("utf8"))
    message = message.hexdigest()

    addr = smileycoin.getAddress()
    sig = smileycoin.signMessage(addr, message)
    return Response("""
Your Identity: %s


-----BEGIN SMILEYCOIN SIGNED MESSAGE-----
%s
-----BEGIN SIGNATURE-----
%s
%s
-----END SMILEYCOIN SIGNED MESSAGE-----
    """.strip() % (
        user_identity,
        message,
        addr,
        sig,
    ), status=200, content_type="text/plain")


def utcnow():
    return datetime.datetime.utcnow()


def view_award(request):
    """Show coins awarded to student"""
    student = get_current_student(request)
    data = request.json_body if request.body else {}

    (lastAwardTime, walletId, coinClaimed) = (DBSession.query(
        func.max(Base.classes.coin_award.award_time),
        func.max(Base.classes.coin_award.wallet),  # TODO: Should be last, not max
        func.sum(Base.classes.coin_award.amount),
    )
        .filter_by(user_id=student.user_id)
        .first())
    if coinClaimed is None:
        lastAwardTime = 0
        coinClaimed = 0
        walletId = ''

    history = []
    coinAwarded = 0

    for row in DBSession.execute(
            "SELECT a.time_end, a.coins_awarded, s.title"
            "  FROM answer a, stage s"
            " WHERE a.stage_id = s.stage_id"
            "   AND a.user_id = :user_id"
            "   AND coins_awarded > 0"
            " ORDER BY a.time_end, s.title"
            "", dict(
                user_id=student.user_id,
            )):
        coinAwarded += row[1]
        history.insert(0, dict(
            lecture=row[2],
            time=datetime_to_timestamp(row[0]) if row[1] else None,
            amount=row[1],
            claimed=(coinAwarded <= coinClaimed and row[0] <= lastAwardTime)
        ))

    # Check if wallet ID is provided, if so pay up.
    txId = None
    if data is not None and data.get('walletId', None):
        walletId = data['walletId']
    # Check if wallet ID is provided, if so pay up.
    txId = None
    if data is not None and data.get('walletId', None):
        walletId = data['walletId']

        # Validate Captcha if not a unittest wallet
        if walletId.startswith('$$UNITTEST'):
            pass
        elif walletId == '$$DONATE:EIAS':
            walletId = 'BPj18BBacYdvEnqgJqKVRNFQrw5ka76gxy'
        elif request.registry.settings.get('tutorweb.captcha.key', None):
            from norecaptcha import captcha

            res = captcha.submit(
                data.get('captchaResponse', ''),
                request.registry.settings.get('tutorweb.captcha.key', None),
                request.client_addr,
            )
            if res.error_code:
                raise ValueError("Could not validate CAPTCHA")
            elif not res.is_valid:
                raise ValueError("Invalid CAPTCHA")

        # Have we already given out our maximum for today?
        dailyTotalAward = (DBSession.query(func.sum(Base.classes.coin_award.amount))
                                    .filter(Base.classes.coin_award.award_time > (utcnow() - datetime.timedelta(days=1)))
                                    .one())[0] or 0
        if dailyTotalAward > MAX_DAILY_AWARD:
            raise ValueError("We have distributed all awards available for today")

        # Has this student already got their coins for the hour?
        hourlyStudentTotal = (DBSession.query(func.sum(Base.classes.coin_award.amount))
                                       .filter(Base.classes.coin_award.user_id == student.user_id)
                                       .filter(Base.classes.coin_award.award_time > (utcnow() - datetime.timedelta(hours=1)))
                                       .one())[0] or 0
        coinOwed = min(
            coinAwarded - coinClaimed,
            MAX_STUDENT_HOURLY_AWARD - hourlyStudentTotal,
        )
        if coinOwed == 0 and (coinAwarded - coinClaimed) > 0:
            raise ValueError("You cannot redeem any more awards just yet")

        # Perform transaction
        txId = smileycoin.sendTransaction(walletId, coinOwed)

        # Worked, so update database
        DBSession.add(Base.classes.coin_award(
            user_id=student.user_id,
            amount=int(coinOwed),
            wallet=walletId,
            tx=txId,
            award_time=utcnow(),  # NB: So it gets mocked in the tests
        ))
        DBSession.flush()

        # Worked, so should be even now
        for h in history:
            h['claimed'] = True
        coinClaimed += coinOwed

    return dict(
        walletId=walletId,
        history=history,
        coin_available=int(coinAwarded - coinClaimed),
        tx_id=txId,
    )


def includeme(config):
    config.add_view(view_totalcoin, route_name='coin_totalcoin')
    config.add_view(view_verifystudent, route_name='coin_verifystudent')
    config.add_view(view_award, route_name='coin_award', renderer='json')
    config.add_route('coin_totalcoin', '/coin/totalcoin')
    config.add_route('coin_verifystudent', '/coin/verifystudent')
    config.add_route('coin_award', '/coin/award')
