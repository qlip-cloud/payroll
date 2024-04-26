import frappe
from frappe.utils import add_to_date, getdate, now, get_time
from frappe import _

# Global Cosntants
CONST_JOURNAL= "Journal Entry"
CONST_FINANCE_BOOK = "BASE"
CONST_NAMING_SERIES = "ACC-JV-.YYYY.-"
CONST_PARTY_TYPE = "Supplier"

def entry_journal_orchestrator(doc):

    # Consulta asientos contables relacionados con el diario
    get_temporal_data = frappe.db.sql(f'SELECT * FROM tabQp_Payroll_Designer_Data_Temp WHERE temporal_lot = "{doc.name}" ORDER BY name ASC', as_dict=1)
    
    # Validar debitos y creditos
    get_sum = frappe.db.sql(f'SELECT SUM(debit_value) as debe, SUM(credit_value) as haber FROM tabQp_Payroll_Designer_Data_Temp WHERE temporal_lot = "{doc.name}" ORDER BY name ASC', as_dict=1)

    for data in get_sum:
        if data.debe != data.haber:
            difference_sum = data.debe - data.haber
            return True, f"Total Debit must be equal to Total Credit. The difference is {difference_sum}"


    ## Validando datos de tabla principal
    try:
        company = frappe.db.get_value('Company', frappe.db.get_value("Global Defaults", None, "default_company"), "company_name")
    except frappe.exceptions.DoesNotExistError as exc_company:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"No se encontro el nombre de la compañia - {exc_company}"

    # Nuevo objeto diario
    new_obj_journal_entry = set_journal_entry(doc, CONST_JOURNAL, CONST_NAMING_SERIES, CONST_FINANCE_BOOK, company)

    # Setear los asientos contables relacionados al libro diario
    for index, row in enumerate(get_temporal_data):
        error, msg, object_account_entries = new_account_entries(doc, index, row)

        if not error:
            new_obj_journal_entry["accounts"].append(object_account_entries)
        else:
            return error, msg

    # Insertar nuevo doctype
    set_journal_entry_doc = frappe.get_doc(new_obj_journal_entry)
    set_journal_entry_doc.insert()

    # Confirmar transaccion
    frappe.db.commit()

    return False, None

def set_journal_entry(doc, voucher_type, naming_series, finance_book, company):
    
    return {
        "doctype": "Journal Entry",
        "voucher_type": voucher_type,
        "naming_series": naming_series,
        "finance_book": finance_book, 
        "company": company,
        "posting_date": now(),
        "accounts": [],
    }
    
def new_account_entries(doc, index, row):
     
     ## Validando datos que van a tabla hija
    try:
        account = frappe.get_last_doc("Account", filters={"account_number": row.account})
    except frappe.exceptions.DoesNotExistError as exc_account:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"La cuenta no existe - {exc_account}", None

    try:
        customer = frappe.get_last_doc("Customer", filters={"tax_id":row.nit})
    except frappe.exceptions.DoesNotExistError as exc_customer:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"El tercero no existe id: {row.nit}{exc_customer}", None
    
    try:
        temp_cost_center = row.cost_center if row.cost_center != "" else "00"
        cost_center = frappe.get_last_doc("Cost Center", filters={"cost_center_name":temp_cost_center})
    except frappe.exceptions.DoesNotExistError as exc_cost_center:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"El centro de costo no existe - {exc_cost_center}", None
    
    try:
        float(row.debit_value)
    except ValueError as exc:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"El valor del debe no es flotante - {exc}", None
    
    try:
        float(row.credit_value)
    except ValueError as exc:
        frappe.log_error(message=frappe.get_traceback(), title="journal_entry_process")
        frappe.db.rollback()
        return True, f"El valor del haber no es flotante - {exc}", None    
    
    # Objeto account
    return False, None, {
        "account": account.name,
        "party_type": CONST_PARTY_TYPE,
        "party": customer.name,
        "cost_center": cost_center.name,
        "debit_in_account_currency": float(row.debit_value),
        "credit_in_account_currency": float(row.credit_value)
    }