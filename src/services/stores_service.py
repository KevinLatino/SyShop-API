import sanic
from sanic.exceptions import SanicException
from models.users import Store, Customer
from models.accounts import GoogleAccount
from models.location import Location
from models.store_multimedia_item import StoreMultimediaItem
from utilities.sessions import create_session_for_user
from utilities.accounts import create_plain_account, does_google_account_exist
from utilities.web import download_file_in_base64
from utilities.stripe import create_stripe_account

stores_service = sanic.Blueprint(
    "StoresService",
    url_prefix="stores_service"
)


def create_store_multimedia_items(store, content_bytes_list):
    for content_bytes in content_bytes_list:
        store_multimedia_item = StoreMultimediaItem(
            content_bytes=content_bytes
        ).save()

        store.multimedia.connect(store_multimedia_item)


def create_store(store, location, multimedia_items):
    stripe_account = create_stripe_account()
    stored_location = Location(**location).save()
    stored_store = Store(
        **store,
        stripe_account_id=stripe_account["id"]
    ).save()

    stored_store.location.connect(stored_location)

    create_store_multimedia_items(stored_store, multimedia_items)

    return store


def make_store_from_google_user_information(user_information):
    picture_url = user_information["picture"]

    name = user_information["given_name"]
    phone_number = user_information["phone_number"]
    picture = download_file_in_base64(picture_url)
    stripe_account = create_stripe_account()

    store = Store(
        name=name,
        description="",
        picture=picture,
        phone_number=phone_number,
        stripe_account_id=stripe_account["id"]
    ).save()

    return store


@stores_service.post("/sign_up_store_with_plain_account")
def sign_up_store_with_plain_account(request):
    email = request.json.pop("email")
    password = request.json.pop("password")
    multimedia_items = request.json.pop("multimedia")
    store_location = request.json.pop("location")

    plain_account = create_plain_account(email, password)
    store = create_store(
        store=request.json,
        location=store_location,
        multimedia_items=multimedia_items
    )

    store.account.connect(plain_account)

    json = create_session_for_user(store)

    return sanic.json(json)


@stores_service.post("/sign_up_store_with_google_account")
def sign_up_store_with_google_account(request):
    google_unique_identifier = request.json.pop("google_unique_identifier")
    store_location = request.json.pop("location")
    multimedia_items = request.json.pop("multimedia")

    if does_google_account_exist(google_unique_identifier):
        raise SanicException("GOOGLE_ACCOUNT_ALREADY_EXISTS")

    store = create_store(
        store=request.json,
        location=store_location,
        multimedia_items=multimedia_items
    )
    google_account = GoogleAccount(
        google_unique_identifier=google_unique_identifier
    )

    store.account.connect(google_account)

    json = create_session_for_user(store)

    return sanic.json(json)


@stores_service.post("/update_store")
def update_store(request):
    store_id = request.json.pop("store_id")
    multimedia_items = request.json.pop("multimedia")

    store = Store.nodes.first(user_id=store_id)

    for store_multimedia_item in store.multimedia.all():
        store_multimedia_item.delete()

    create_store_multimedia_items(store, multimedia_items)

    store.name = request.json["name"]
    store.description = request.json["description"]
    store.phone_number = request.json["phone_number"]
    store.picture = request.json["picture"]

    store.save()

    return sanic.empty()


@stores_service.post("/follow_store")
def follow_store(request):
    store_id = request.json["store_id"]
    customer_id = request.json["customer_id"]

    customer = Customer.nodes.first(user_id=customer_id)
    store = Store.nodes.first(user_id=store_id)

    store.followers.connect(customer)

    return sanic.empty()


@stores_service.post("/get_store_by_id")
def get_store_by_id(request):
    store_id = request.json["store_id"]

    store = Store.nodes.first(user_id=store_id)
    multimedia_items = [
        store_multimedia_item.content_bytes
        for store_multimedia_item in store.multimedia.all()
    ]
    account_type = store.account.single().__class__.__name__

    json = {
        **store.__properties__,
        "multimedia": multimedia_items,
        "account_type": account_type
    }

    return sanic.json(json)


@stores_service.post("/search_stores_by_name")
def search_stores_by_name(request):
    start = request.json["start"]
    amount = request.json["amount"]
    searched_name = request.json["search"]

    search_results = Store.nodes.filter(
        name__icontains=searched_name
    )[start:amount]

    json = [
        store.__properties__
        for store in search_results
    ]

    return sanic.json(json)
