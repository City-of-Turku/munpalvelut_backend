"""
Email sending utilities
"""

from __future__ import absolute_import, unicode_literals

from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import get_script_prefix
from django.template.loader import get_template
from django.template import Context, TemplateDoesNotExist
from django.utils import translation
from django.conf import settings

import smtplib
import types

import logging
logger = logging.getLogger(__name__)

def send_template_mail(recipient, template, variables, sender=None, html=True, subject=None):
    """
    Send an e-mail using a template.

    Arguments:
    recipient -- the address(es) of the recipient(s)
    template  -- the template name to use. See below for details.
    variables -- a dictionary of variables to use in the template context.
    sender    -- the sender address. If not specified, a built-in default
                 will be used.
    html      -- if set to False, no HTML part will be used even if available.
    subject   -- if not None, this will be used as the message subject instead
                 of the subject template.

    In case of failure, a log entry is printed and False returned.

    Template name:

    The template will be searched from the "email" subdirectory of the template
    directory. The extensions ".html" and ".txt" will be tried. The
    ".txt" template must be present. The HTML template, if present, will
    be used as the message's alternative content.

    A template named "(template name).subject" will be used as the message
    subject.

    Context:

    The dictionary given as argument will be made available to the templates.
    In addition, the following keys will also be available (unless overriden
    by the user passed dictionary.)

    recipient   -- the address of the recipient
    sender      -- the address of the sender
    """

    if isinstance(recipient, str):
        recipient = (recipient,)
    elif isinstance(recipient, types.GeneratorType):
        recipient = tuple(recipient)

    if not recipient:
        logger.info("Not sending template mail (%s) to any recipient from %s", template, sender)
        return False

    sender = sender or getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@sofokus.com')

    lang = translation.get_language()

    logger.info("Sending template mail (%s) to %s from %s in language %s",
        template, list(recipient), sender, lang)

    #siteroot = get_siteroot()

    ctx = {
        'recipient': recipient,
        'sender': sender,
        #'SITE_ROOT': siteroot,
        #'STATIC_URL': siteroot + settings.STATIC_URL,
    }
    ctx.update(variables)

    if subject is None:
        subject = _get_localized_template(template, lang, "subject").render(ctx).strip()
    plaintext = _get_localized_template(template, lang, "txt").render(ctx)

    alttext = None
    if html:
        try:
            alttext = _get_localized_template(template, lang, "html").render(ctx)
        except TemplateDoesNotExist:
            # HTML part is optional
            pass

    msg = EmailMultiAlternatives(subject, plaintext, sender, recipient)
    if alttext:
        msg.attach_alternative(alttext, "text/html")

    try:
        msg.send()
    except smtplib.SMTPException as ex:
        logger.error("Error while sending e-mail to %s: %s", recipient, ex)
        return False
    return True

def _get_localized_template(name, language, suffix):
    """
    Internal: Get the best version of the template for the given language.
    The search order is:
    template_XX-XX.suffix
    template_XX.suffix
    template.suffix
    """
    try:
        if language:
            return get_template("email/{}_{}.{}".format(name, language, suffix))
        else:
            return get_template("email/{}.{}".format(name, suffix))

    except TemplateDoesNotExist:
        if not language:
            raise
        elif '-' in language:
            return _get_localized_template(name, language.split('-')[0], suffix)
        else:
            return _get_localized_template(name, '', suffix)

def send_template_admin_mail(subject, template, variables):
    """
    This is a convenience function that works much like Django's builtin
    mail_admins, except it uses the send_template_mail function.
    Unlike in send_template_mail, the subject parameter is required.
    It will automatically be prefixed with EMAIL_SUBJECT_PREFIX.

    The message is sent to all administrators defined in settings.py.

    The message is always sent using the system default language.

    Arguments:
    subject   -- the message subject.
    template  -- name of the template to use
    variables -- a dictionary of variables to use in the template context.
    """

    with translation.override(settings.LANGUAGE_CODE):
        send_template_mail(
            (a[1] for a in settings.ADMINS),
            template,
            variables,
            subject=settings.EMAIL_SUBJECT_PREFIX + subject,
            lang=settings.LANGUAGE_CODE
            )

def send_template_manager_mail(subject, template, variables):
    """
    Like send_template_admin_mail, except mail is sent to the
    addresses defined in the MANAGERS instead of ADMINS setting.

    Arguments:
    subject   -- the message subject.
    template  -- name of the template to use
    variables -- a dictionary of variables to use in the template context.
    """

    with translation.override(settings.LANGUAGE_CODE):
        send_template_mail(
            (a[1] for a in settings.MANAGERS),
            template,
            variables,
            subject=settings.EMAIL_SUBJECT_PREFIX + subject,
            lang=settings.LANGUAGE_CODE
            )
