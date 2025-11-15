from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, Response, current_app
from datetime import datetime
from weasyprint import HTML
from models import db, Customer, Item, Invoice, InvoiceItem, get_global_setting
from helpers.api_helpers import get_arn_number, process_invoice
from utils import login_required, calculate_invoice_totals, recalculate_invoice_totals, indian_currency_filter
import os

invoice_bp = Blueprint(
    'invoice', 
    __name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    url_prefix='/invoices'
)


#--------------------------------HELPER FUNCTIONS--------------------------------

def serialize_invoice(invoice, include_items=True):
    data = {
        "id": invoice.id,
        "customer": invoice.customer.name if invoice.customer else None,
        "customer_id": invoice.customer.id if invoice.customer else None,
        "created_at": str(invoice.created_at),
        "subtotal": invoice.subtotal,
        "gst_amount": invoice.gst_amount,
        "total": invoice.total,
        "applied_gst": invoice.applied_gst,
        "gst_percent_used": invoice.gst_percent_used,
        "arn_number": invoice.arn_number,
    }
    
    if include_items:
        data["items"] = [
            serialize_invoice_item(ii) for ii in invoice.invoice_items
        ]
    
    return data


def serialize_invoice_item(invoice_item):
    return {
        "id": invoice_item.id,
        "item_id": invoice_item.item.id,
        "item_name": invoice_item.item.name,
        "quantity": invoice_item.quantity,
        "unit_price": invoice_item.unit_price,
        "amount": invoice_item.amount
    }


def serialize_invoice_detailed(invoice):
    data = serialize_invoice(invoice, include_items=False)
    data.update({
        "customer": {
            "id": invoice.customer.id,
            "name": invoice.customer.name,
            "email": invoice.customer.email,
            "phone": invoice.customer.phone
        },
        "arn_generated_at": str(invoice.arn_generated_at) if invoice.arn_generated_at else None,
        "modified_after_arn": invoice.modified_after_arn,
        "items": [serialize_invoice_item(ii) for ii in invoice.invoice_items]
    })
    return data


def validate_invoice_data(data):
    customer_id = data.get("customer_id")
    items = data.get("items", [])
    
    if not customer_id:
        return False, "Customer is required"
    
    if not items:
        return False, "At least one item is required"
    
    return True, None


def generate_invoice_arn(customer_name, invoice_id=None):
    if invoice_id:
        temp_invoice_number = f"INV-{invoice_id:06d}"
    else:
        temp_invoice_number = f"TEMP-{int(datetime.now().timestamp())}"
    
    return get_arn_number(customer_name, temp_invoice_number, invoice_id=invoice_id)


def create_invoice_with_items(customer, items_data, arn_number):
    global_setting = get_global_setting()
    
    invoice = Invoice.create(
        customer=customer,
        created_at=datetime.now(),
        arn_number=arn_number,
        arn_generated_at=datetime.now(),
        applied_gst=global_setting.apply_gst,
        gst_percent_used=global_setting.gst_percent,
        subtotal=0,
        gst_amount=0,
        total=0
    )
    
    create_invoice_items(invoice, items_data)
    recalculate_invoice_totals(invoice)
    
    return invoice


def create_invoice_items(invoice, items_data):
    for item_data in items_data:
        item = Item.get_by_id(item_data["item_id"])
        unit_price = item_data.get("unit_price", item.price)
        quantity = item_data["quantity"]
        
        InvoiceItem.create(
            invoice=invoice,
            item=item,
            quantity=quantity,
            unit_price=unit_price,
            amount=unit_price * quantity
        )


def update_invoice_items(invoice, items_data):
    InvoiceItem.delete().where(InvoiceItem.invoice == invoice).execute()
    create_invoice_items(invoice, items_data)


def update_invoice_customer(invoice, customer_id):
    customer = Customer.get_by_id(customer_id)
    invoice.customer = customer
    invoice.save()
    return customer


def prepare_pdf_items(invoice_items):
    return [
        {
            "item_name": ii.item.name,
            "quantity": ii.quantity,
            "unit_price": indian_currency_filter(ii.unit_price),
            "amount": indian_currency_filter(ii.amount)
        }
        for ii in invoice_items
    ]


def prepare_pdf_totals(invoice):
    return {
        "subtotal": indian_currency_filter(invoice.subtotal),
        "gst_amount": indian_currency_filter(invoice.gst_amount),
        "total": indian_currency_filter(invoice.total)
    }


def render_invoice_pdf(invoice):
    invoice_items = InvoiceItem.select().where(InvoiceItem.invoice == invoice)
    items = prepare_pdf_items(invoice_items)
    totals = prepare_pdf_totals(invoice)
    
    html = render_template(
        "invoice_pdf.html",
        invoice=invoice,
        customer=invoice.customer,
        items=items,
        subtotal=totals["subtotal"],
        gst_amount=totals["gst_amount"],
        gst_percent=invoice.gst_percent_used,
        apply_gst=invoice.applied_gst,
        total=totals["total"]
    )
    
    return HTML(string=html).write_pdf()


#--------------------------------API ROUTES--------------------------------

@invoice_bp.route('/', methods=['GET'])
@login_required
def get_invoices():
    invoices = Invoice.select().order_by(Invoice.created_at.desc())
    data = [serialize_invoice(inv) for inv in invoices]
    return jsonify(data)


@invoice_bp.route("/api/<int:invoice_id>", methods=["GET"])
@login_required
def get_invoice(invoice_id):
    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    
    return jsonify(serialize_invoice_detailed(invoice))


@invoice_bp.route("/", methods=["POST"])
@login_required
def create_invoice():
    data = request.get_json()
    
    # Validate input
    is_valid, error_message = validate_invoice_data(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    try:
        customer = Customer.get_by_id(data["customer_id"])
        
        # Generate ARN
        try:
            arn_number = generate_invoice_arn(customer.name)
        except Exception as e:
            return jsonify({"error": f"ARN generation failed. Please retry. ({str(e)})"}), 500

        # Create invoice with items
        with db.atomic():
            invoice = create_invoice_with_items(customer, data["items"], arn_number)

        return jsonify({
            "invoice_id": invoice.id,
            "arn_number": arn_number,
            "subtotal": invoice.subtotal,
            "gst_amount": invoice.gst_amount,
            "total": invoice.total,
            "message": "Invoice created successfully with ARN and GST info"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoice_bp.route('/api/<int:invoice_id>', methods=['PUT'])
@login_required
def update_invoice(invoice_id):
    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    data = request.get_json()
    
    try:
        with db.atomic():
            # Update customer if provided
            if 'customer_id' in data:
                update_invoice_customer(invoice, data['customer_id'])
            
            # Update items if provided
            if 'items' in data:
                update_invoice_items(invoice, data['items'])
            
            # Recalculate totals
            recalculate_invoice_totals(invoice)
        
        return jsonify({
            "message": "Invoice updated successfully",
            "invoice_id": invoice.id,
            "subtotal": invoice.subtotal,
            "gst_amount": invoice.gst_amount,
            "total": invoice.total,
            "modified_after_arn": invoice.modified_after_arn
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@invoice_bp.route('/api/<int:id>', methods=['DELETE'])
@login_required
def delete_invoice(id):
    invoice = Invoice.get_or_none(Invoice.id == id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    try:
        invoice.delete_instance(recursive=True)
        return jsonify({"message": "Invoice deleted successfully"})
    except Exception:
        return jsonify({"error": "Error deleting invoice"}), 500


@invoice_bp.route('/<int:invoice_id>/generate_arn', methods=['POST'])
@login_required
def generate_arn(invoice_id):
    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    if invoice.arn_number:
        return jsonify({
            "message": "ARN already generated",
            "arn_number": invoice.arn_number,
            "generated_at": str(invoice.arn_generated_at)
        }), 200

    try:
        arn = generate_invoice_arn(invoice.customer.name, invoice.id)

        invoice.arn_number = arn
        invoice.arn_generated_at = datetime.now()
        invoice.modified_after_arn = False
        invoice.save()

        return jsonify({
            "message": "ARN generated successfully",
            "arn_number": arn,
            "generated_at": str(invoice.arn_generated_at)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@invoice_bp.route('/process_invoice/<int:invoice_id>', methods=['POST'])
@login_required
def process_invoice_route(invoice_id):
    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    try:
        result = process_invoice(invoice_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@invoice_bp.route('/generate_pdf', methods=["POST"])
@login_required
def generate_pdf():
    data = request.get_json()
    invoice_id = data.get("invoice_id")

    if not invoice_id:
        return jsonify({"error": "invoice_id is required"}), 400

    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    try:
        pdf = render_invoice_pdf(invoice)

        return Response(
            pdf,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"inline; filename=invoice_{invoice.id}.pdf"}
        )

    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


#--------------------------------PAGE ROUTES--------------------------------

@invoice_bp.route("/<int:invoice_id>", methods=["GET"])
@login_required
def view_invoice(invoice_id):
    back_url = request.args.get("back", url_for('invoice.invoices_page'))

    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        flash("Invoice not found", "error")
        return redirect(url_for('invoice.invoices_page'))

    items = list(InvoiceItem.select().where(InvoiceItem.invoice == invoice))

    return render_template(
        "invoice_detail.html",
        invoice=invoice,
        customer=invoice.customer,
        items=items,
        subtotal=invoice.subtotal,
        gst_amount=invoice.gst_amount,
        total=invoice.total,
        apply_gst=invoice.applied_gst,
        gst_percent=invoice.gst_percent_used,
        back_url=back_url,
    )


@invoice_bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice_page(invoice_id):
    invoice = Invoice.get_or_none(Invoice.id == invoice_id)
    if not invoice:
        flash("Invoice not found", "error")
        return redirect(url_for('invoice.invoices_page'))

    if request.method == "POST":
        try:
            with db.atomic():
                # Update customer if changed
                customer_id = request.form.get('customer_id')
                if customer_id:
                    update_invoice_customer(invoice, int(customer_id))
                
                # Prepare items data from form
                items_data = []
                item_ids = request.form.getlist('item_id[]')
                quantities = request.form.getlist('quantity[]')
                unit_prices = request.form.getlist('unit_price[]')
                
                for item_id, quantity, unit_price in zip(item_ids, quantities, unit_prices):
                    if item_id and quantity:
                        item = Item.get_by_id(int(item_id))
                        items_data.append({
                            "item_id": int(item_id),
                            "quantity": int(quantity),
                            "unit_price": float(unit_price) if unit_price else item.price
                        })
                
                # Update items
                update_invoice_items(invoice, items_data)
                recalculate_invoice_totals(invoice)
            
            flash("Invoice updated successfully", "success")
            return redirect(url_for('invoice.invoices_page'))
        
        except Exception as e:
            flash(f"Error updating invoice: {str(e)}", "error")
            return redirect(url_for('invoice.edit_invoice_page', invoice_id=invoice_id))

    customers = Customer.select().order_by(Customer.name.asc())
    all_items = Item.select().order_by(Item.name.asc())
    invoice_items = list(InvoiceItem.select().where(InvoiceItem.invoice == invoice))

    return render_template(
        'edit_invoice.html',
        invoice=invoice,
        customers=customers,
        all_items=all_items,
        invoice_items=invoice_items
    )


@invoice_bp.route('_page')
@login_required
def invoices_page():
    invoices = Invoice.select().join(Customer).order_by(Invoice.created_at.desc())
    return render_template('invoices.html', invoices=invoices, current_page='invoices_page')