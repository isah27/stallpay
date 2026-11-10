from .. import config
from .live import LivePaypalClient
from .mock import MockPaypalClient


def make_paypal_client():
    if config.paypal_is_live():
        return LivePaypalClient()
    return MockPaypalClient(config.PUBLIC_BASE_URL)
