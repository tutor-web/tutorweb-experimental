import calendar
import datetime


def timestamp_to_datetime(ts):
    return datetime.datetime.utcfromtimestamp(ts)


def datetime_to_timestamp(dt):
    return calendar.timegm(dt.timetuple())
