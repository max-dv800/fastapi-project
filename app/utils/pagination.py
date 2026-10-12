from sqlalchemy import select

from app.models import Event


def price_not_none(price):
    data = []
    order_by = [Event.price.asc()]

    match price:
        case "paid":
            data.append(Event.price > 0)
        case "less_than_5000":
            data.append(Event.price < 5000)
        case "free":
            data.append(Event.price == 0)

    return data, order_by


def start_date_not_none(start_date):
    order_by = []

    match start_date:
        case "earlier":
            order_by.append(Event.start_time.asc())
        case "later":
            order_by.append(Event.start_time.desc())

    return order_by


def query_sql(status, price=None, start_date=None, skip=0, limit=10):
    data = [Event.status == status]

    price_data, price_order = price_not_none(price)
    data.extend(price_data)

    order_by = start_date_not_none(start_date) + price_order

    stmt = select(Event).where(*data).offset(skip).limit(limit)
    if order_by is not None:
        stmt = stmt.order_by(*order_by)

    return stmt
