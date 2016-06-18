# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Event, EventProcessingException, Transfer, Charge, Plan
from .models import Invoice, InvoiceItem, Subscription, Customer


class CustomerHasSourceListFilter(admin.SimpleListFilter):
    title = "source presence"
    parameter_name = "has_source"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Source"],
            ["no", "Does Not Have Source"]
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(default_source=None)
        if self.value() == "no":
            return queryset.filter(default_source=None)


class InvoiceCustomerHasSourceListFilter(admin.SimpleListFilter):
    title = "source presence"
    parameter_name = "has_source"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Source"],
            ["no", "Does Not Have Source"]
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(customer__default_source=None)
        if self.value() == "no":
            return queryset.filter(customer__default_source=None)


class CustomerSubscriptionStatusListFilter(admin.SimpleListFilter):
    title = "subscription status"
    parameter_name = "sub_status"

    def lookups(self, request, model_admin):
        statuses = [
            [x, x.replace("_", " ").title()]
            for x in Subscription.objects.all().values_list(
                "status",
                flat=True
            ).distinct()
        ]
        statuses.append(["none", "No Subscription"])
        return statuses

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.all()
        else:
            return queryset.filter(subscriptions__status=self.value()).distinct()


def send_charge_receipt(modeladmin, request, queryset):
    """
    Function for sending receipts from the admin if a receipt is not sent for
    a specific charge.
    """
    for charge in queryset:
        charge.send_receipt()


admin.site.register(
    Charge,
    list_display=[
        "stripe_id",
        "customer",
        "amount",
        "description",
        "paid",
        "disputed",
        "refunded",
        "fee",
        "receipt_sent",
        "stripe_timestamp",
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "invoice__stripe_id",
    ],
    list_filter=[
        "paid",
        "disputed",
        "refunded",
        "stripe_timestamp",
    ],
    raw_id_fields=[
        "customer",
    ],
    actions=(send_charge_receipt,),
)

admin.site.register(
    EventProcessingException,
    list_display=[
        "message",
        "event",
        "created"
    ],
    search_fields=[
        "message",
        "traceback",
        "data"
    ],
)

admin.site.register(
    Event,
    raw_id_fields=["customer"],
    list_display=[
        "stripe_id",
        "type",
        "livemode",
        "valid",
        "processed",
        "stripe_timestamp"
    ],
    list_filter=[
        "type",
        "created",
        "valid",
        "processed"
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "validated_message"
    ],
)


class SubscriptionInline(admin.TabularInline):
    model = Subscription


def subscription_status(customer):
    """
    Returns a string representation of the customer's subscription status.
    If the customer does not have a subscription, an empty string is returned.
    """

    if customer.subscription:
        return customer.subscription.status
    else:
        return ""
subscription_status.short_description = "Subscription Status"


def cancel_subscription(modeladmin, request, queryset):
    """Cancels a subscription."""

    for subscription in queryset:
        subscription.cancel()
cancel_subscription.short_description = "Cancel selected subscriptions"

admin.site.register(
    Subscription,
    raw_id_fields=[
        "customer",
        "plan",
    ],
    list_display=[
        "stripe_id",
        "status",
        "stripe_timestamp",
    ],
    list_filter=[
        "status",
    ],
    search_fields=[
        "stripe_id",
    ],
    actions=[cancel_subscription]
)


admin.site.register(
    Customer,
    raw_id_fields=["subscriber"],
    list_display=[
        "stripe_id",
        "subscriber",
        subscription_status,
        "stripe_timestamp"
    ],
    list_filter=[
        CustomerHasSourceListFilter,
        CustomerSubscriptionStatusListFilter
    ],
    search_fields=[
        "stripe_id"
    ],
    inlines=[SubscriptionInline]
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem


def customer_has_source(obj):
    """ Returns True if the customer has a source attached to its account."""
    return obj.customer.default_source is not None
customer_has_source.short_description = "Customer Has Source"


def customer_email(obj):
    """ Returns a string representation of the customer's email."""
    return str(obj.customer.subscriber.email)
customer_email.short_description = "Customer"


admin.site.register(
    Invoice,
    raw_id_fields=["customer"],
    readonly_fields=('stripe_timestamp',),
    list_display=[
        "stripe_id",
        "paid",
        "forgiven",
        "closed",
        customer_email,
        customer_has_source,
        "period_start",
        "period_end",
        "subtotal",
        "total",
        "stripe_timestamp"
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id"
    ],
    list_filter=[
        InvoiceCustomerHasSourceListFilter,
        "paid",
        "forgiven",
        "closed",
        "attempted",
        "attempt_count",
        "stripe_timestamp",
        "date",
        "period_end",
        "total"
    ],
    inlines=[InvoiceItemInline]
)


admin.site.register(
    Transfer,
    list_display=[
        "stripe_id",
        "amount",
        "status",
        "date",
        "description",
        "stripe_timestamp"
    ],
    search_fields=[
        "stripe_id",
    ]
)


class PlanAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        """Update or create objects using our custom methods that
        sync with Stripe."""

        if change:
            obj.update_name()

        else:
            Plan.get_or_create(**form.cleaned_data)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:
            readonly_fields.extend([
                'stripe_id',
                'amount',
                'currency',
                'interval',
                'interval_count',
                'trial_period_days'])

        return readonly_fields

admin.site.register(Plan, PlanAdmin)
