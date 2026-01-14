"""
Twilio SMS Module

Provides SMS sending and webhook handling via Twilio.
"""

from .models import SendSMSRequest, SendSMSResponse, InboundSMS, MessageDirection, MessageStatus
from .executor import TwilioSMSExecutor

__all__ = [
    'SendSMSRequest',
    'SendSMSResponse',
    'InboundSMS',
    'MessageDirection',
    'MessageStatus',
    'TwilioSMSExecutor'
]

__version__ = '1.0.0'
