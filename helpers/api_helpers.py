import requests
import time
from datetime import datetime
from models import APIErrorLog, Invoice
import logging

# Logging setup
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

# API Configuration
API_URL = "https://buildwithhussain.com/api/v2/method/get_arn_number"
API_KEY = "2c70587e2df4779"
API_SECRET = "56331804ac8ca7b"


def log_api_error(invoice_id, api_name, error_message, full_response):
    try:
        invoice = None
        if invoice_id:
            invoice = Invoice.get_or_none(Invoice.id == invoice_id)

        # Truncate very long responses to avoid DB issues
        response_str = str(full_response)
        if len(response_str) > 10000:
            response_str = response_str[:10000] + "... [TRUNCATED]"

        APIErrorLog.create(
            invoice=invoice,
            api_name=api_name,
            error_message=f"{error_message}\n\nFull Response:\n{response_str}",
            timestamp=datetime.now()
        )
        logger.info(f" Logged API error for invoice #{invoice_id}")
    except Exception as e:
        logger.error(f" Could not log API error: {str(e)}")


def get_arn_number(user_name, invoice_number, invoice_id=None, max_retries=3):
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }

    payload = {
        "user_name": user_name,
        "invoice_number": invoice_number
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} for invoice #{invoice_id}")
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)

            # Success case
            if response.status_code == 200:
                data = response.json()
                arn_number = data.get("arn_number") or data.get("message", {}).get("arn_number")
                
                if arn_number:
                    logger.info(f" ARN generated successfully: {arn_number}")
                    return arn_number
                else:
                    error_msg = "ARN not found in API response"
                    log_api_error(invoice_id, "get_arn_number", error_msg, response.text)
                    raise Exception(error_msg)

            # if Authentication failure - dont retry
            elif response.status_code == 401:
                error_msg = "Authentication failed - Invalid API credentials"
                log_api_error(invoice_id, "get_arn_number", error_msg, response.text)
                logger.error(f"✗ {error_msg}")
                raise Exception(error_msg)

            # Other HTTP errors - retry with backoff
            else:
                try:
                    err_data = response.json()
                    error_message = err_data.get("message", "Unknown error")
                except Exception:
                    error_message = "Unknown error"
                
                log_api_error(invoice_id, "get_arn_number", f"HTTP {response.status_code}: {error_message}", response.text)
                logger.warning(f" Attempt {attempt} failed with HTTP {response.status_code}: {error_message}")
                
                if attempt == max_retries:
                    raise Exception(f"Failed after {max_retries} attempts: {error_message}")
                
                wait_time = 2 ** (attempt - 1)
                logger.info(f" Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        except requests.exceptions.Timeout:
            logger.warning(f" Request timeout on attempt {attempt}")
            if attempt == max_retries:
                raise Exception("Failed after max retries: Request timeout")
            time.sleep(2 ** (attempt - 1))

        except requests.exceptions.RequestException as e:
            logger.error(f" Network error: {str(e)}")
            if attempt == max_retries:
                raise Exception(f"Failed after max retries: {str(e)}")
            time.sleep(2 ** (attempt - 1))

        except Exception as e:
            error_str = str(e)
            logger.error(f" Unexpected error: {error_str}")
            
            if "Authentication failed" in error_str:
                raise
            
            if attempt == max_retries:
                raise
            
            time.sleep(2 ** (attempt - 1))

    # never reaching this logically, but just in case
    raise Exception("ARN generation failed - unknown error")


def process_invoice(invoice_id):
    try:
        invoice = Invoice.get_or_none(Invoice.id == invoice_id)
        if not invoice:
            logger.error(f"Invoice #{invoice_id} not found")
            return {"error": "Invoice not found"}

        # Check if ARN already exists
        if invoice.arn_number:
            logger.info(f"Invoice #{invoice_id} already has ARN: {invoice.arn_number}")
            return {
                "message": "Invoice already processed",
                "arn_number": invoice.arn_number,
                "generated_at": str(invoice.arn_generated_at)
            }

        # Generate new ARN
        customer_name = invoice.customer.name
        invoice_number = f"INV-{invoice.id:06d}"
        
        logger.info(f"Generating ARN for invoice #{invoice_id} ({customer_name})")
        arn_number = get_arn_number(customer_name, invoice_number, invoice_id)

        # Update invoice with ARN
        invoice.arn_number = arn_number
        invoice.arn_generated_at = datetime.now()
        invoice.save()

        logger.info(f"✓ Invoice #{invoice_id} processed successfully with ARN: {arn_number}")
        return {
            "message": "Invoice processed successfully",
            "arn_number": arn_number,
            "generated_at": str(invoice.arn_generated_at)
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"✗ Error processing invoice #{invoice_id}: {error_msg}")
        return {"error": error_msg}