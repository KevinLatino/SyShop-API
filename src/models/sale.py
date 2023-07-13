from neomodel import (
    StructuredNode,
    StringProperty,
    IntegerProperty,
    DateTimeProperty,
    UniqueIdProperty,
    Relationship
)


class Sale(StructuredNode):
    sale_id = UniqueIdProperty()
    amount = IntegerProperty(required=True)
    purchase_date = DateTimeProperty(required=False)
    stripe_payment_intent_id = StringProperty(unique_index=True, required=True)

    post = Relationship("models.sale.Sale", "SOLD")
    delivery = Relationship("models.delivery.Delivery", "DELIVERS")
    customer = Relationship("models.users.Customer", "BOUGHT")
