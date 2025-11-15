from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from peewee import IntegrityError
from models import Customer, Invoice
from utils import login_required

customer_bp = Blueprint(
    'customer',
    __name__,
    template_folder='templates',
    url_prefix='/customers'
)


#--------------------------------HELPER FUNCTIONS--------------------------------

def serialize_customer(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone
    }


def validate_customer_data(data, is_update=False):
    errors = []
    
    name = data.get('name', '').strip() if 'name' in data else None
    
    # Validate name
    if not is_update and not name:
        errors.append("Name is required")
    elif name is not None and not name:
        errors.append("Name cannot be empty")
    
    return len(errors) == 0, errors


def sanitize_customer_data(data):
    sanitized = {}
    
    if 'name' in data:
        sanitized['name'] = data['name'].strip()
    
    if 'email' in data:
        email = data['email'].strip()
        sanitized['email'] = email if email else None
    
    if 'phone' in data:
        phone = data['phone'].strip()
        sanitized['phone'] = phone if phone else None
    
    return sanitized


def create_customer_from_data(data):
    sanitized = sanitize_customer_data(data)
    return Customer.create(**sanitized)


def update_customer_from_data(customer, data):
    sanitized = sanitize_customer_data(data)
    
    for key, value in sanitized.items():
        setattr(customer, key, value)
    
    customer.save()
    return customer


def get_customer_invoices(customer):
    return Invoice.select().where(
        Invoice.customer == customer
    ).order_by(Invoice.created_at.desc())

#--------------------------------API ROUTES--------------------------------

@customer_bp.route('/', methods=['GET'])
@login_required
def get_customers():
    customers = Customer.select().order_by(Customer.id.desc())
    return jsonify([serialize_customer(c) for c in customers])


@customer_bp.route('/', methods=['POST'])
@login_required
def create_customer():
    data = request.get_json(silent=True) or {}
    
    is_valid, errors = validate_customer_data(data)
    if not is_valid:
        return jsonify({"error": ", ".join(errors)}), 400

    try:
        customer = create_customer_from_data(data)
        return jsonify({
            "message": "Customer created successfully",
            "id": customer.id,
            "customer": serialize_customer(customer)
        }), 201
    except IntegrityError:
        return jsonify({"error": "Database error creating customer"}), 500


@customer_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    return jsonify(serialize_customer(customer))


@customer_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json() or {}
    
    is_valid, errors = validate_customer_data(data, is_update=True)
    if not is_valid:
        return jsonify({"error": ", ".join(errors)}), 400

    try:
        customer = update_customer_from_data(customer, data)
        return jsonify({
            "message": "Customer updated successfully",
            "customer": serialize_customer(customer)
        })
    except IntegrityError:
        return jsonify({"error": "Database error updating customer"}), 500


@customer_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    try:
        customer.delete_instance(recursive=True)
        return jsonify({"message": "Customer deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Error deleting customer: {str(e)}"}), 500


#--------------------------------PAGE ROUTES--------------------------------

@customer_bp.route('/_page')
@login_required
def customers_page():
    customers = Customer.select().order_by(Customer.id.desc())
    return render_template(
        'customers.html',
        customers=customers,
        current_page='customers_page'
    )


@customer_bp.route('/_page/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.get_or_none(Customer.id == customer_id)
    if not customer:
        flash("Customer not found", "error")
        return redirect(url_for('customer.customers_page'))

    invoices = get_customer_invoices(customer)

    return render_template(
        'customer_detail.html',
        customer=customer,
        invoices=invoices
    )


@customer_bp.route('/_page/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer_page(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        flash("Customer not found", "error")
        return redirect(url_for('customer.customers_page'))

    if request.method == "POST":
        data = {
            'name': request.form.get('name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', '')
        }
        
        is_valid, errors = validate_customer_data(data, is_update=False)
        if not is_valid:
            for error in errors:
                flash(error, "error")
            return redirect(url_for('customer.edit_customer_page', id=id))

        try:
            update_customer_from_data(customer, data)
            flash("Customer updated successfully", "success")
            return redirect(url_for('customer.customers_page'))
        except Exception as e:
            flash(f"Error updating customer: {str(e)}", "error")
            return redirect(url_for('customer.edit_customer_page', id=id))

    return render_template('edit_customer.html', customer=customer)


@customer_bp.route('/_page/<int:customer_id>/invoices')
@login_required
def customer_invoices(customer_id):
    customer = Customer.get_or_none(Customer.id == customer_id)
    if not customer:
        flash("Customer not found", "error")
        return redirect(url_for('customer.customers_page'))

    invoices = get_customer_invoices(customer)
    back_url = request.args.get("back", url_for('customer.customers_page'))

    return render_template(
        'customer_invoices.html',
        customer=customer,
        invoices=invoices,
        back_url=back_url
    )