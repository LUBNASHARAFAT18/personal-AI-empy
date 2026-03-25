"""
Odoo MCP Server - Model Context Protocol for Odoo Accounting Integration

Provides JSON-RPC API for:
- Creating invoices
- Recording payments
- Fetching financial reports
- Managing customers/vendors
- Account reconciliation

Usage:
    docker-compose up -d odoo-mcp
    curl http://localhost:8809/health
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('odoo_mcp')

app = Flask(__name__)

# Odoo configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'postgres')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

# MCP Server configuration
MCP_PORT = int(os.getenv('MCP_PORT', '8809'))


class OdooClient:
    """Client for Odoo JSON-RPC API."""
    
    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.uid = None
        self.session = requests.Session()
    
    def authenticate(self) -> bool:
        """Authenticate with Odoo."""
        try:
            # Odoo JSON-RPC authentication
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.user, self.password, {}]
                },
                "id": 1
            }
            
            response = self.session.post(
                f"{self.url}/web/session/authenticate",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            if result.get('result', {}).get('uid'):
                self.uid = result['result']['uid']
                logger.info(f"Authenticated with Odoo as user {self.uid}")
                return True
            else:
                logger.error("Odoo authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def execute(self, model: str, method: str, *args, **kwargs):
        """Execute Odoo model method."""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Not authenticated")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.db,
                        self.uid,
                        self.password,
                        model,
                        method,
                        list(args),
                        kwargs
                    ]
                },
                "id": 2
            }
            
            response = self.session.post(
                f"{self.url}/web/dataset/call_kw",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            if 'error' in result:
                raise Exception(result['error'].get('data', {}).get('message', 'Unknown error'))
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise


# Initialize Odoo client
odoo_client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'odoo_connected': odoo_client.uid is not None
    })


@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """
    MCP (Model Context Protocol) endpoint.
    Handles requests from AI Employee for Odoo operations.
    """
    try:
        data = request.json
        action = data.get('action')
        params = data.get('params', {})
        
        logger.info(f"MCP Request: {action}")
        
        # Route to appropriate handler
        if action == 'create_invoice':
            result = create_invoice(params)
        elif action == 'record_payment':
            result = record_payment(params)
        elif action == 'get_invoices':
            result = get_invoices(params)
        elif action == 'get_financial_report':
            result = get_financial_report(params)
        elif action == 'create_customer':
            result = create_customer(params)
        elif action == 'get_account_summary':
            result = get_account_summary(params)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown action: {action}'
            }), 400
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"MCP Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_invoice(params: dict) -> dict:
    """
    Create an invoice in Odoo.
    
    Params:
        - partner_id: Customer ID
        - invoice_date: Invoice date (YYYY-MM-DD)
        - due_date: Due date (YYYY-MM-DD)
        - lines: List of {product_id, quantity, price_unit}
    """
    invoice_lines = []
    for line in params.get('lines', []):
        invoice_lines.append((0, 0, {
            'product_id': line.get('product_id'),
            'quantity': line.get('quantity', 1),
            'price_unit': line.get('price_unit', 0),
            'name': line.get('name', 'Service')
        }))
    
    invoice_data = {
        'move_type': 'out_invoice',
        'partner_id': params.get('partner_id'),
        'invoice_date': params.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
        'invoice_date_due': params.get('due_date'),
        'invoice_line_ids': invoice_lines,
        'state': 'draft'
    }
    
    invoice_id = odoo_client.execute('account.move', 'create', invoice_data)
    
    logger.info(f"Created invoice {invoice_id}")
    
    return {
        'invoice_id': invoice_id,
        'status': 'draft',
        'message': f'Invoice {invoice_id} created successfully'
    }


def record_payment(params: dict) -> dict:
    """
    Record a payment in Odoo.
    
    Params:
        - invoice_id: Invoice ID to pay
        - amount: Payment amount
        - payment_date: Payment date
        - payment_method: Payment method
    """
    payment_data = {
        'partner_type': 'customer',
        'payment_type': 'inbound',
        'partner_id': params.get('partner_id'),
        'amount': params.get('amount', 0),
        'payment_date': params.get('payment_date', datetime.now().strftime('%Y-%m-%d')),
        'journal_id': params.get('journal_id', 1)  # Default to bank journal
    }
    
    payment_id = odoo_client.execute('account.payment', 'create', payment_data)
    odoo_client.execute('account.payment', 'action_post', [payment_id])
    
    logger.info(f"Recorded payment {payment_id}")
    
    return {
        'payment_id': payment_id,
        'status': 'posted',
        'message': f'Payment {payment_id} recorded successfully'
    }


def get_invoices(params: dict) -> list:
    """
    Get invoices from Odoo.
    
    Params:
        - state: Invoice state (draft, posted, cancel)
        - partner_id: Filter by customer
        - limit: Maximum results
    """
    domain = []
    
    if params.get('state'):
        domain.append(('state', '=', params['state']))
    if params.get('partner_id'):
        domain.append(('partner_id', '=', params['partner_id']))
    
    invoices = odoo_client.execute(
        'account.move',
        'search_read',
        domain=domain,
        fields=['name', 'partner_id', 'amount_total', 'amount_due', 'invoice_date', 'state'],
        limit=params.get('limit', 50)
    )
    
    return invoices


def get_financial_report(params: dict) -> dict:
    """
    Get financial report from Odoo.
    
    Params:
        - report_type: 'balance_sheet', 'profit_loss', 'aged_receivable'
        - date_from: Start date
        - date_to: End date
    """
    report_type = params.get('report_type', 'balance_sheet')
    
    # Simplified financial report
    report = {
        'report_type': report_type,
        'generated_at': datetime.now().isoformat(),
        'data': {}
    }
    
    if report_type == 'balance_sheet':
        # Get total receivables and payables
        receivables = odoo_client.execute(
            'account.move',
            'search_read',
            domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
            fields=['amount_total', 'amount_residual']
        )
        
        total_receivable = sum(inv['amount_residual'] for inv in receivables)
        
        report['data'] = {
            'total_receivables': total_receivable,
            'total_invoices': len(receivables)
        }
    
    elif report_type == 'profit_loss':
        # Get income and expenses
        income_moves = odoo_client.execute(
            'account.move',
            'search_read',
            domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
            fields=['amount_total']
        )
        
        expense_moves = odoo_client.execute(
            'account.move',
            'search_read',
            domain=[('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
            fields=['amount_total']
        )
        
        total_income = sum(inv['amount_total'] for inv in income_moves)
        total_expense = sum(inv['amount_total'] for inv in expense_moves)
        
        report['data'] = {
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': total_income - total_expense
        }
    
    return report


def create_customer(params: dict) -> dict:
    """
    Create a customer in Odoo.
    
    Params:
        - name: Customer name
        - email: Email address
        - phone: Phone number
        - vat: VAT number
    """
    customer_data = {
        'name': params.get('name'),
        'email': params.get('email'),
        'phone': params.get('phone'),
        'vat': params.get('vat'),
        'customer_rank': 1
    }
    
    customer_id = odoo_client.execute('res.partner', 'create', customer_data)
    
    logger.info(f"Created customer {customer_id}")
    
    return {
        'customer_id': customer_id,
        'message': f'Customer {customer_id} created successfully'
    }


def get_account_summary(params: dict) -> dict:
    """
    Get account summary from Odoo.
    
    Returns:
        Summary of accounts, receivables, payables
    """
    # Get unpaid invoices
    unpaid_invoices = odoo_client.execute(
        'account.move',
        'search_read',
        domain=[('state', '=', 'posted'), ('payment_state', '!=', 'paid')],
        fields=['name', 'partner_id', 'amount_total', 'amount_residual', 'invoice_date_due']
    )
    
    total_receivable = sum(inv['amount_residual'] for inv in unpaid_invoices)
    overdue_invoices = [inv for inv in unpaid_invoices if inv.get('invoice_date_due')]
    
    return {
        'total_receivables': total_receivable,
        'unpaid_invoices_count': len(unpaid_invoices),
        'overdue_invoices': overdue_invoices,
        'summary': f'{len(unpaid_invoices)} unpaid invoices totaling ${total_receivable:.2f}'
    }


if __name__ == '__main__':
    logger.info(f"Starting Odoo MCP Server on port {MCP_PORT}")
    logger.info(f"Odoo URL: {ODOO_URL}")
    
    # Test Odoo connection
    if odoo_client.authenticate():
        logger.info("Connected to Odoo successfully")
    else:
        logger.warning("Could not connect to Odoo - will retry on first request")
    
    app.run(host='0.0.0.0', port=MCP_PORT, debug=False)
