from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from peewee import IntegrityError
from models import Item, InvoiceItem, Invoice
from utils import login_required

item_bp = Blueprint(
    'item',
    __name__,
    template_folder='templates',
    url_prefix='/items'
)


#--------------------------------HELPER FUNCTIONS--------------------------------

def serialize_item(item):
    return {
        "id": item.id,
        "name": item.name,
        "price": item.price
    }


def validate_item_data(data, is_update=False):
    errors = []
    
    name = data.get('name', '').strip() if 'name' in data else None
    price = data.get('price')
    
    # Validate name
    if not is_update and not name:
        errors.append("Name is required")
    elif name is not None and not name:
        errors.append("Name cannot be empty")
    
    # Validate price
    if price is not None:
        try:
            price_float = float(price)
            if price_float <= 0:
                errors.append("Price must be greater than 0")
        except (TypeError, ValueError):
            errors.append("Price must be a valid number")
    elif not is_update:
        errors.append("Price is required")
    
    return len(errors) == 0, errors


def create_item_from_data(data):
    name = data.get('name').strip()
    price = float(data.get('price'))
    
    return Item.create(name=name, price=price)


def update_item_from_data(item, data):
    if 'name' in data:
        name = data['name'].strip()
        if name:
            item.name = name
    
    if 'price' in data:
        price = float(data['price'])
        if price > 0:
            item.price = price
    
    item.save()
    return item


def delete_item_with_references(item):
    InvoiceItem.delete().where(InvoiceItem.item == item).execute()
    item.delete_instance()


def get_item_invoice_history(item):
    return (
        InvoiceItem.select(InvoiceItem, Invoice)
        .join(Invoice)
        .where(InvoiceItem.item == item)
        .order_by(Invoice.created_at.desc())
    )


#--------------------------------API ROUTES--------------------------------

@item_bp.route('/', methods=['GET'])
@login_required
def get_items():
    items = Item.select().order_by(Item.id.desc())
    return jsonify([serialize_item(i) for i in items])


@item_bp.route('/', methods=['POST'])
@login_required
def create_item():
    data = request.get_json(silent=True) or {}
    
    is_valid, errors = validate_item_data(data)
    if not is_valid:
        return jsonify({"error": ", ".join(errors)}), 400

    try:
        item = create_item_from_data(data)
        return jsonify({
            "message": "Item created successfully",
            "id": item.id,
            "item": serialize_item(item)
        }), 201
    except IntegrityError:
        return jsonify({"error": "Database error creating item"}), 500


@item_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_item(id):
    item = Item.get_or_none(Item.id == id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    return jsonify(serialize_item(item))


@item_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_item(id):
    item = Item.get_or_none(Item.id == id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json() or {}
    
    is_valid, errors = validate_item_data(data, is_update=True)
    if not is_valid:
        return jsonify({"error": ", ".join(errors)}), 400

    try:
        item = update_item_from_data(item, data)
        return jsonify({
            "message": "Item updated successfully",
            "item": serialize_item(item)
        })
    except IntegrityError:
        return jsonify({"error": "Database error updating item"}), 500


@item_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_item(id):
    item = Item.get_or_none(Item.id == id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        delete_item_with_references(item)
        return jsonify({"message": "Item deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Error deleting item: {str(e)}"}), 500


#--------------------------------PAGE ROUTES--------------------------------

@item_bp.route('_page')
@login_required
def items_page():
    items = Item.select().order_by(Item.id.desc())
    return render_template(
        'items.html',
        items=items,
        current_page='items_page'
    )


@item_bp.route('/_page/<int:item_id>')
@login_required
def item_detail(item_id):
    item = Item.get_or_none(Item.id == item_id)
    if not item:
        flash("Item not found", "error")
        return redirect(url_for('item.items_page'))

    invoice_items = get_item_invoice_history(item)

    return render_template(
        'item_detail.html',
        item=item,
        invoice_items=invoice_items
    )


@item_bp.route('/_page/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item_page(id):
    item = Item.get_or_none(Item.id == id)
    if not item:
        flash("Item not found", "error")
        return redirect(url_for('item.items_page'))

    if request.method == "POST":
        data = {
            'name': request.form.get("name", "").strip(),
            'price': request.form.get("price", "")
        }
        
        is_valid, errors = validate_item_data(data, is_update=False)
        if not is_valid:
            for error in errors:
                flash(error, "error")
            return redirect(url_for('item.edit_item_page', id=id))

        try:
            update_item_from_data(item, data)
            flash("Item updated successfully", "success")
            return redirect(url_for('item.items_page'))
        except Exception as e:
            flash(f"Error updating item: {str(e)}", "error")
            return redirect(url_for('item.edit_item_page', id=id))

    return render_template('edit_item.html', item=item)