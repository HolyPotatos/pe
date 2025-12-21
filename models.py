class Orders:
    def __init__(self, id, date, address, seller_id, storekeeper_id, client_id, delivery_type, order_type, order_status, payment_type, payment_status, total_price):
        self.ID = id
        self.Date = date
        self.DeliveryAddress = address
        self.SellerID = seller_id
        self.StorekeeperID = storekeeper_id
        self.ClientID = client_id
        self.DeliveryType = delivery_type
        self.OrderType = order_type
        self.OrderStatus = order_status
        self.PaymentType = payment_type
        self.PaymentStatus = payment_status
        self.TotalPrice = total_price