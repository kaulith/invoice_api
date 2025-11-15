import os
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, session
from peewee import fn

from models import Customer, Item, Invoice, InvoiceItem
from utils import (
    login_required,
    inject_theme,
    indian_currency_filter,
    format_currency
)

# Import blueprints
from blueprints.customer.customer import customer_bp
from blueprints.item.item import item_bp
from blueprints.invoice.invoice import invoice_bp
from blueprints.setting.settings import settings_bp
from blueprints.auth.auth import auth_bp


# --- Flask App Setup ---
app = Flask(__name__)
app.config.from_object('config')

# Ensure secret key (for sessions & flash)
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Session lifetime
app.permanent_session_lifetime = timedelta(days=7)


# --- Register Global Filters and Context Processors ---
app.jinja_env.filters['indian_currency'] = indian_currency_filter
app.jinja_env.filters['format_currency'] = format_currency
app.context_processor(inject_theme)


# --- Register Blueprints ---
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(item_bp)
app.register_blueprint(invoice_bp)
app.register_blueprint(settings_bp)


@app.route('/')
def index():
    """Redirect root to login page"""
    return redirect(url_for('auth.auth_page', mode='login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with stats"""
    app.logger.info(f"Dashboard SESSION: {session}")

    total_customers = Customer.select().count()
    total_items = Item.select().count()
    total_invoices = Invoice.select().count()
    total_sales = (
        InvoiceItem
        .select(fn.SUM(InvoiceItem.amount))
        .join(Invoice)
        .scalar() or 0
    )

    return render_template(
        'dashboard.html',
        total_customers=total_customers,
        total_items=total_items,
        total_invoices=total_invoices,
        total_sales=total_sales,
        current_page='dashboard'
    )


@app.route('/add/<string:entity_type>')
@login_required
def add_entity_page(entity_type):
    valid_entities = {'customer', 'item', 'invoice'}
    if entity_type not in valid_entities:
        return "Invalid entity", 400

    context = {
        'hide_add_button': True,
        'entity_type': entity_type,
        'customers': [],
        'items': []   
    }

    if entity_type == "invoice":
        context['customers'] = list(Customer.select().order_by(Customer.name.asc()))
        context['items'] = list(Item.select().order_by(Item.name.asc()))   

    return render_template('add_entity.html', **context)


if __name__ == '__main__':
    app.run(debug=True)
