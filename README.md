# SMS-Activate Email API

This is an unofficial API wrapper for `sms-activate.org` temporary mailboxes service.

## API v2
V1 API was deprecated on sms-activate, now here are 2 classes `SMSActivateEmailClientV1` and
`SMSActivateEmailClientV2`. 

`SMSActivateEmailClient` now is just a child of `SMSActivateEmailClientV2`.

## Example
```python
from sms_activate_email.client import SMSActivateEmailClient, EmailDomain, EmailDomainType

sms_activate_email_client = SMSActivateEmailClient('YOUR_API_KEY')  # Init client 
activation = sms_activate_email_client.buy_email_activation(
    from_domain='sms-activate.org', domain=EmailDomain('outlook.com', EmailDomainType.POPULAR)
)  # Buy activation

activation_email = activation.email  # Email got for your mailbox
message_text = activation.get_text(period_sec=5, attempts=12)  # Will check for email for 1 minute (5*12=60)
message_text = activation.full_message  # This is also an option to get message text after get_text() was called

# After email was received you can reactivate your mailbox to get new email
activation.reactivate()
message_text = activation.get_text(period_sec=5, attempts=12)  # Will check for email for 1 minute (5*12=60)
message_text = activation.full_message  # This is also an option to get message text after get_text() was called
```
