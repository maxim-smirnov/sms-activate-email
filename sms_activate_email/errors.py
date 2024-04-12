class SMSActivateError(Exception):
    pass


class BadAPIKeyError(SMSActivateError):
    pass


class BadActionError(SMSActivateError):
    pass


class BadBalanceError(SMSActivateError):
    pass


class BadSiteError(SMSActivateError):
    pass


class BadDomainError(SMSActivateError):
    pass


class ChannelsLimitError(SMSActivateError):
    pass


class ActivationNotFoundError(SMSActivateError):
    pass


class WaitingForMessageError(SMSActivateError):
    pass