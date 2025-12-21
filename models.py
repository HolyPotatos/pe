class Orders:
    def __init__(self, id, date, address, seller_id, storekeeper_id, delivery_type, order_status, payment_type, total_price):
        self.ID = id
        self.Date = date
        self.DeliveryAddress = address
        self.SellerID = seller_id
        self.StorekeeperID = storekeeper_id
        self.DeliveryType = delivery_type
        self.OrderStatus = order_status
        self.PaymentType = payment_type
        self.TotalPrice = total_price
    
class OrderParts:
    def __init__(self, part_id, sku, title, order_id, count, unit_retail_price):
        self.PartID = part_id
        self.SKU = sku
        self.Title = title
        self.OrderID = order_id
        self.Count = count
        self.UnitRetailPrice = unit_retail_price

class OrderHistory:
    def __init__(self, id, date_time, old_value, new_value, order_id):
        self.ID = id
        self.Date = date_time 
        self.OldValue = old_value
        self.NewValue = new_value
        self.OrderID = order_id

class AutoPart:
    def __init__(self, id, sku, title, brand_name, stock, retail_price):
        self.Id = id
        self.Sku = sku
        self.Title = title
        self.BrandName = brand_name
        self.Stock = stock
        self.RetailPrice = retail_price

class NavigationItem:
    def __init__(self, id, title, type_level):
        self.Id = id
        self.Title = title
        self.TypeLevel = type_level