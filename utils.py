from functools import wraps
from decimal import Decimal
from flask import session, request, jsonify, redirect, url_for, flash
from models import User, UserSetting


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for('auth.auth_page', mode='login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.get_or_none(User.id == user_id)


def recalculate_invoice_totals(invoice):
    subtotal = sum(Decimal(str(item.amount)) for item in invoice.invoice_items)
    gst_amount = Decimal('0')
    
    if invoice.applied_gst:
        gst_amount = (subtotal * Decimal(str(invoice.gst_percent_used))) / Decimal('100')
        gst_amount = gst_amount.quantize(Decimal('0.01'))
    
    total = subtotal + gst_amount
    
    # Update the invoice with calculated values
    invoice.subtotal = float(subtotal)
    invoice.gst_amount = float(gst_amount)
    invoice.total = float(total)
    
    # Mark as modified if ARN was already generated
    if invoice.arn_number:
        invoice.modified_after_arn = True
    
    invoice.save()
    
    return float(subtotal), float(gst_amount), float(total)


def get_invoice_totals(invoice):
    return invoice.subtotal, invoice.gst_amount, invoice.total


def calculate_invoice_totals(invoice):
    return invoice.subtotal, invoice.gst_amount, invoice.total


def indian_currency_filter(value):
    try:
        value = float(value)
        s = f"{value:.2f}"
        parts = s.split('.')
        whole = parts[0]
        decimal = parts[1] if len(parts) > 1 else '00'
        
        if len(whole) > 3:
            last_three = whole[-3:]
            remaining = whole[:-3]
            groups = []
            while remaining:
                if len(remaining) >= 2:
                    groups.insert(0, remaining[-2:])
                    remaining = remaining[:-2]
                else:
                    groups.insert(0, remaining)
                    remaining = ''
            whole = ','.join(groups) + ',' + last_three
        
        return f"{whole}.{decimal}"
    except (ValueError, TypeError):
        return value


def format_currency(value):
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return value


def inject_theme():
    user_id = session.get('user_id')
    if user_id:
        user = User.get_or_none(User.id == user_id)
        if user:
            user_setting = UserSetting.get_or_none(UserSetting.user == user)
            if user_setting:
                return {'theme': user_setting.theme}
    return {'theme': 'light'}