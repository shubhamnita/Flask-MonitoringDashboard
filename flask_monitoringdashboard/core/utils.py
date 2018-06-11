import ast

import numpy as np
from flask import url_for
from werkzeug.routing import BuildError

from flask_monitoringdashboard import config
from flask_monitoringdashboard.core.rules import get_rules
from flask_monitoringdashboard.core.timezone import to_local_datetime
from flask_monitoringdashboard.database.count import count_requests, count_total_requests
from flask_monitoringdashboard.database.endpoint import get_endpoint_by_id
from flask_monitoringdashboard.database.request import get_date_of_first_request


def get_endpoint_details(db_session, endpoint_id):
    """ Return details about an endpoint"""
    endpoint = get_endpoint_by_id(db_session, endpoint_id)
    endpoint.last_requested = to_local_datetime(endpoint.last_requested)
    endpoint.time_added = to_local_datetime(endpoint.time_added)
    return {
        'id': endpoint_id,
        'endpoint': endpoint.name,
        'rules': ', '.join([r.rule for r in get_rules(endpoint.name)]),
        'rule': endpoint,
        'url': get_url(endpoint.name),
        'total_hits': count_requests(db_session, endpoint.id)
    }


def get_details(db_session):
    """ Return details about the deployment """
    import json
    from flask_monitoringdashboard import loc
    with open(loc() + 'constants.json', 'r') as f:
        constants = json.load(f)

    return {
        'link': config.link,
        'dashboard-version': constants['version'],
        'config-version': config.version,
        'first-request': get_date_of_first_request(db_session),
        'total-requests': count_total_requests(db_session)
    }


def get_url(end):
    """
    Returns the URL if possible.
    URL's that require additional arguments, like /static/<file> cannot be retrieved.
    :param end: the endpoint for the url.
    :return: the url_for(end) or None,
    """
    try:
        return url_for(end)
    except BuildError:
        return None


def simplify(values, n=5):
    """
    Simplify a list of values. It returns a list that is representative for the input
    :param values: list of values
    :param n: length of the returned list
    :return: list with n values: min, q1, median, q3, max
    """
    return [np.percentile(values, i * 100 // (n - 1)) for i in range(n)]