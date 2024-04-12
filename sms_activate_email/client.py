import enum
import functools
import json
from builtins import type
from datetime import datetime

import requests
import time
import typing


from sms_activate_email.errors import (
    SMSActivateError, BadAPIKeyError, BadActionError, BadBalanceError,
    BadSiteError, BadDomainError, ChannelsLimitError, ActivationNotFoundError,
    WaitingForMessageError
)


class EmailDomainType(enum.Enum):
    """
    Enumeration of possible domain types for temporary mailbox.
    """
    ZONES = 1
    POPULAR = 2


class EmailDomain:
    """
    Represents a temporary mailbox domain.

    Attributes
    ----------
    name : str
        the domain name e.g. 'example.com'; or zone name e.g. 'xyz'
    type : EmailDomainType
        the type of the domain
    cost : float
        the cost of the mailbox in this domain
    count : int
        the number of available mailboxes in this domain, not applicable for zones type domains
    """
    name: str
    type: EmailDomainType
    cost: float
    count: int

    def __init__(self, name: str, type: EmailDomainType, cost: float = -1, count: int = -1):
        self.name = name
        self.type = type
        self.cost = cost
        self.count = count

    def __str__(self):
        return f'{self.name}'


class EmailActivation:
    """
    Represents a temporary mailbox (email activation).

    `id` and `email` attributes are always filled, other attributes can be `None`.

    Attributes
    ----------
    id : int
        the activation id got from sms-activate
    email : str
        the mailbox email
    site : str
        the domain from which the mailbox is expecting the message
    status : int
        the status of the activation (lack of info from sms-activate)
    value : str
        the value of the activation (lack of info from sms-activate)
    cost : float
        the price of this mailbox
    date : datetime
        the datetime when the mailbox was created or reactivated
    full_message : str
        the full message got by this mailbox
    """
    id: int
    email: str

    site: typing.Union[str, None] = None
    status: typing.Union[int, None] = None
    value: typing.Union[str, None] = None
    cost: typing.Union[float, None] = None
    date: typing.Union[datetime, None] = None
    full_message: typing.Union[str, None] = None

    def __init__(
            self,
            id: int,
            email: str,
            site: typing.Union[str, None] = None,
            status: typing.Union[int, None] = None,
            value: typing.Union[str, None] = None,
            cost: typing.Union[float, None] = None,
            date: typing.Union[datetime, None] = None,
            full_message: typing.Union[str, None] = None
    ):
        self.id = id
        self.email = email
        self.site = site
        self.status = status
        self.value = value
        self.cost = cost
        self.date = date
        self.full_message = full_message

    def get_text(self, period_sec: int = 5, attempts: int = 10) -> str:
        """
        Returns the text of the message got by this activation.
        :param period_sec: How much time to wait between activation checks.
        :param attempts: How many attempts to perform to get the message.
        :return: The text of the message.
        """
        raise NotImplemented()

    def reactivate(self) -> bool:
        """
        Reactivates the mailbox to receive a new message. The `id` attribute will be changed.
        :return: Is the mailbox successfully reactivated.
        """
        raise NotImplemented()

    def cancel(self) -> bool:
        """
        Cancels the mailbox.
        :return: Is the mailbox successfully canceled.
        """
        raise NotImplemented()

    def __str__(self):
        return f'#{self.id}: {self.email}'


class SMSActivateEmailClient:
    """
    Represents an `sms-activate` API client for temporary mailboxes.
    """
    def __init__(self, api_key: str, base_url: str = 'https://api.sms-activate.org/stubs/handler_api.php'):
        """
        :param api_key: Your API key for SMS-Activate.
        :param base_url: API base URL.
        """
        self._api_key = api_key
        self._base_url = base_url

        self._session = requests.Session()
        self._session.headers = {'User-Agent': 'python-sms-activate-email/0.1'}
        self._session.params = {'api_key': self._api_key}

    @staticmethod
    def _response_to_dict(response: requests.Response) -> dict:
        """
        Converts SMS-Activate response to dictionary and checks for API errors.
        :param response: Requests response object.
        :return: Dictionary with response data.
        """
        if response.status_code != 200:
            raise SMSActivateError('Bad status code: {}'.format(response.status_code))

        try:
            response_dict = response.json()
        except json.decoder.JSONDecodeError:
            raise SMSActivateError('Bad json: {}'.format(response.text))

        if 'error' in response_dict:
            if response_dict['error'] == 'BAD_KEY':
                raise BadAPIKeyError
            if response_dict['error'] == 'BAD_ACTION':
                raise BadActionError
            if response_dict['error'] == 'BAD_BALANCE':
                raise BadBalanceError
            if response_dict['error'] == 'BAD_SITE' or response_dict['error'] == 'BLOCKED_SITE':
                raise BadSiteError
            if response_dict['error'] == 'MAIL_TYPE_ERROR':
                raise BadDomainError
            if response_dict['error'] == 'CHANNELS_LIMIT':
                raise ChannelsLimitError
            if response_dict['error'] == 'ACTIVATION_NOT_FOUND' or response_dict['error'] == 'NO_ACTIVATION':
                raise ActivationNotFoundError
            if response_dict['error'] == 'WAIT_LINK':
                raise WaitingForMessageError

        if response_dict.get('status', None) != 'OK':
            raise SMSActivateError('Bad status: {}'.format(response_dict.get('status', None)))

        return response_dict['response']

    def get_available_domains(self, from_domain: str) -> typing.List[EmailDomain]:
        """
        Get a list of available domains for temporary mailbox.
        :param from_domain: Domain from which you are expecting to receive an email.
        :return: List of available domains.
        """
        response = self._session.get(self._base_url, params={'action': 'getDomains', 'site': from_domain})
        response_dict = self._response_to_dict(response)
        domains = [
            EmailDomain(
                domain['name'],
                EmailDomainType.ZONES,
                domain['cost'],
                domain.get('count', -1)
            ) for domain in response_dict.get('zones', [])
        ]
        domains += [
            EmailDomain(
                domain['name'],
                EmailDomainType.POPULAR,
                domain['cost'],
                domain.get('count', -1)
            ) for domain in response_dict.get('popular', [])
        ]
        return domains

    def get_email_activations(self, page=1, per_page=10, search=None, sort='desc') -> typing.List[EmailActivation]:
        """
        Returns the list of currently active email activations.
        :param page: The page number to get.
        :param per_page: The number of activations per page.
        :param search: The mailbox email to search for.
        :param sort: The sorting order by `id` attribute. `asc` or `desc`.
        :return: List of currently active email activations.
        """
        response = self._session.get(self._base_url, params={
            'action': 'getMailHistory', 'page': page,
            'per_page': per_page, 'search': search, 'sort': sort
        })
        response_dict = self._response_to_dict(response)
        activations = []
        for activation in response_dict['list']:
            activation = EmailActivation(
                id=activation['id'],
                email=activation['email'],
                site=activation['site'],
                status=activation['status'],
                value=activation['value'],
                cost=activation['cost'],
                date=activation['date'],
                full_message=activation['full_message']
            )
            activation.get_text = functools.partial(self._get_email_activation_text, activation)
            activation.reactivate = functools.partial(self._reactivate_email_activation, activation)
            activation.cancel = functools.partial(self._cancel_email_activation, activation)
            activations.append(activation)
        return activations

    def buy_email_activation(self, from_domain: str, domain: EmailDomain) -> EmailActivation:
        """
        Buy a new temporary mailbox.
        :param from_domain: Domain from which you are expecting to receive an email.
        :param domain: Domain for your mailbox. You can get it from `get_available_domains` method or construct
        it manually e.g. `EmailDomain('outlook.com', EmailDomainType.POPULAR)`
        :return: An `EmailActivation` instance.
        """
        response = self._session.get(self._base_url, params={
            'action': 'buyMailActivation', 'site': from_domain,
            'mail_type': domain.type.value, 'mail_domain': domain.name
        })
        response_dict = self._response_to_dict(response)
        activation = EmailActivation(id=response_dict['id'], email=response_dict['email'])
        activation.get_text = functools.partial(self._get_email_activation_text, activation)
        activation.reactivate = functools.partial(self._reactivate_email_activation, activation)
        activation.cancel = functools.partial(self._cancel_email_activation, activation)
        return activation

    def _get_email_activation_text(self, activation: EmailActivation, period_sec: int = 5, attempts: int = 10) -> str:
        for i in range(attempts):
            response = self._session.get(self._base_url, params={'action': 'checkMailActivation', 'id': activation.id})
            response_dict = self._response_to_dict(response)
            if 'full_message' in response_dict:
                activation.full_message = response_dict['full_message']
                return response_dict['full_message']
            time.sleep(period_sec)
        raise TimeoutError('Timed out waiting for text')

    def _reactivate_email_activation(self, activation: EmailActivation) -> bool:
        response = self._session.get(self._base_url, params={'action': 'reorderMailActivation', 'id': activation.id})
        response_dict = self._response_to_dict(response)
        activation.__init__(id=response_dict['id'], email=response_dict['email'])
        return True

    def _cancel_email_activation(self, activation: EmailActivation) -> bool:
        response = self._session.get(self._base_url, params={'action': 'cancelMailActivation', 'id': activation.id})
        response_dict = self._response_to_dict(response)
        return response_dict
