from peewee import (
    Model,
    CharField,
    TextField,
    IntegerField,
    FloatField,
    AutoField,
    DateTimeField,
    ForeignKeyField,
    SQL,
    SqliteDatabase,
    BooleanField
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SqliteDatabase("dev.db")


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = AutoField()
    username = CharField(index=True)
    email = CharField(unique=True, index=True)
    password_hash = CharField()
    created_at = DateTimeField(default=datetime.now)
    last_login = DateTimeField(null=True)
    is_admin = BooleanField(default=False)

    def set_password(self, password):
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserSetting(BaseModel):
    user = ForeignKeyField(User, backref='settings', on_delete='CASCADE', unique=True)
    theme = CharField(default='light')


class GlobalSetting(BaseModel):
    id = AutoField()
    apply_gst = BooleanField(default=False)
    gst_percent = FloatField(default=18.0, constraints=[SQL('CHECK(gst_percent >= 0)')])
    updated_at = DateTimeField(default=datetime.now)


class Customer(BaseModel):
    id = AutoField()
    name = CharField(index=True)
    email = CharField(null=True)
    phone = CharField(null=True)
    created_at = DateTimeField(default=datetime.now)


class Item(BaseModel):
    id = AutoField()
    name = CharField(index=True)
    price = FloatField(constraints=[SQL('CHECK(price >= 0)')])
    created_at = DateTimeField(default=datetime.now)


class Invoice(BaseModel):
    id = AutoField()
    customer = ForeignKeyField(Customer, backref='invoices', on_delete='CASCADE')
    created_at = DateTimeField(default=datetime.now)
    
    subtotal = FloatField(default=0, constraints=[SQL('CHECK(subtotal >= 0)')])
    gst_amount = FloatField(default=0, constraints=[SQL('CHECK(gst_amount >= 0)')])
    total = FloatField(default=0, constraints=[SQL('CHECK(total >= 0)')])
    
    applied_gst = BooleanField(default=False)
    gst_percent_used = FloatField(default=0, constraints=[SQL('CHECK(gst_percent_used >= 0)')])
    
    arn_number = CharField(null=True, default=None)
    einvoice_response = TextField(null=True, default=None)
    arn_generated_at = DateTimeField(null=True, default=None)
    
    modified_after_arn = BooleanField(default=False)


class InvoiceItem(BaseModel):
    id = AutoField()
    invoice = ForeignKeyField(Invoice, backref='invoice_items', on_delete='CASCADE')
    item = ForeignKeyField(Item, backref='invoice_items', on_delete='CASCADE')

    item_name_snapshot = CharField()

    quantity = IntegerField(default=1, constraints=[SQL('CHECK(quantity > 0)')])
    unit_price = FloatField(constraints=[SQL('CHECK(unit_price >= 0)')])
    amount = FloatField(constraints=[SQL('CHECK(amount >= 0)')])

    def save(self, *args, **kwargs):
        if self.quantity and self.unit_price:
            self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class APIErrorLog(BaseModel):
    id = AutoField()
    invoice = ForeignKeyField(Invoice, backref='api_errors', null=True, on_delete='SET NULL')
    api_name = CharField()
    error_message = TextField()
    timestamp = DateTimeField(default=datetime.now)


db.connect()
db.create_tables(
    [User, Customer, Item, Invoice, InvoiceItem, APIErrorLog, UserSetting, GlobalSetting],
    safe=True
)

# Global settings instance
def get_global_setting():
    setting, _ = GlobalSetting.get_or_create(id=1)
    return setting