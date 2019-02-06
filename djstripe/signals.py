"""
signals are sent for each event Stripe sends to the app

Stripe docs for Webhooks: https://stripe.com/docs/webhooks
"""
from django.db.models.signals import pre_delete
from django.dispatch import Signal, receiver

from . import settings as djstripe_settings

webhook_processing_error = Signal(providing_args=["data", "exception"])

# A signal for each Event type. See https://stripe.com/docs/api/events/types

WEBHOOK_SIGNALS = dict(
	[
		(hook, Signal(providing_args=["event"]))
		for hook in [
			"account.updated",
			"account.application.authorized",
			"account.application.deauthorized",
			"account.external_account.created",
			"account.external_account.deleted",
			"account.external_account.updated",
			"application_fee.created",
			"application_fee.refunded",
			"application_fee.refund.updated",
			"balance.available",
			"charge.captured",
			"charge.expired",
			"charge.failed",
			"charge.pending",
			"charge.refunded",
			"charge.succeeded",
			"charge.updated",
			"charge.dispute.closed",
			"charge.dispute.created",
			"charge.dispute.funds_reinstated",
			"charge.dispute.funds_withdrawn",
			"charge.dispute.updated",
			"charge.refund.updated",
			"checkout_beta.session_succeeded",
			"coupon.created",
			"coupon.deleted",
			"coupon.updated",
			"customer.created",
			"customer.deleted",
			"customer.updated",
			"customer.discount.created",
			"customer.discount.deleted",
			"customer.discount.updated",
			"customer.source.created",
			"customer.source.deleted",
			"customer.source.expiring",
			"customer.source.updated",
			"customer.subscription.created",
			"customer.subscription.deleted",
			"customer.subscription.trial_will_end",
			"customer.subscription.updated",
			"file.created",
			"invoice.created",
			"invoice.deleted",
			"invoice.finalized",
			"invoice.marked_uncollectible",
			"invoice.payment_failed",
			"invoice.payment_succeeded",
			"invoice.sent",
			"invoice.upcoming",
			"invoice.updated",
			"invoice.voided",
			"invoiceitem.created",
			"invoiceitem.deleted",
			"invoiceitem.updated",
			"issuing_authorization.created",
			"issuing_authorization.request",
			"issuing_authorization.updated",
			"issuing_card.created",
			"issuing_card.updated",
			"issuing_cardholder.created",
			"issuing_cardholder.updated",
			"issuing_dispute.created",
			"issuing_dispute.updated",
			"issuing_settlement.created",
			"issuing_settlement.updated",
			"issuing_transaction.created",
			"issuing_transaction.updated",
			"order.created",
			"order.payment_failed",
			"order.payment_succeeded",
			"order.updated",
			"order_return.created",
			"payment_intent.amount_capturable_updated",
			"payment_intent.created",
			"payment_intent.payment_failed",
			"payment_intent.requires_capture",
			"payment_intent.succeeded",
			"payout.canceled",
			"payout.created",
			"payout.failed",
			"payout.paid",
			"payout.updated",
			"plan.created",
			"plan.deleted",
			"plan.updated",
			"product.created",
			"product.deleted",
			"product.updated",
			"recipient.created",
			"recipient.deleted",
			"recipient.updated",
			"reporting.report_run.failed",
			"reporting.report_run.succeeded",
			"reporting.report_type.updated",
			"review.closed",
			"review.opened",
			"sigma.scheduled_query_run.created",
			"sku.created",
			"sku.deleted",
			"sku.updated",
			"source.canceled",
			"source.chargeable",
			"source.failed",
			"source.mandate_notification",
			"source.refund_attributes_required",
			"source.transaction.created",
			"source.transaction.updated",
			"topup.canceled",
			"topup.created",
			"topup.failed",
			"topup.reversed",
			"topup.succeeded",
			"transfer.created",
			"transfer.reversed",
			"transfer.updated",
			# deprecated (no longer in events_types list) - TODO can be deleted?
			"issuer_fraud_record.created",
			"subscription_schedule.canceled",
			"subscription_schedule.completed",
			"subscription_schedule.created",
			"subscription_schedule.released",
			"subscription_schedule.updated",
			# special case? - TODO can be deleted?
			"ping",
		]
	]
)


@receiver(pre_delete, sender=djstripe_settings.get_subscriber_model_string())
def on_delete_subscriber_purge_customer(instance=None, **kwargs):
	""" Purge associated customers when the subscriber is deleted. """
	for customer in instance.djstripe_customers.all():
		customer.purge()
