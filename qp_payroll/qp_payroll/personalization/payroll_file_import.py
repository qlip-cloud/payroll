import frappe
from frappe import _

from frappe.utils import now, make_esc
from qp_payroll.qp_payroll.personalization.journal_entry_process import entry_journal_orchestrator
#from milenio_pc.milenio_pc.use_case.sales_invoice_process import sales_invoice_orchestrator
import os

def payroll_file_import(doc):

	error = False
	message = ''
    
	try:
        # Limpieza de tabla temporal
		clear_temporal_data_rows(doc)

        # Carga de data en tabla temporal
		load_return = load_data_infile_to_temporal(doc)
		
		if not load_return == 0:
			
			error = True
			message = "File upload failed. Check the format or content used for the upload."
    
		# Verifica la data en tabla temporal
		count_register = verify_temporal_load_data(doc)

		if not count_register > 0:
			error = True
			message = "Rows not loaded."

		# Llamada a orquestacion
		if not error:
			error = False
			message = "Successfully Completed."

			# Creacion de asiento diario
			try:
				error, message = entry_journal_orchestrator(doc)
				if message:
					message = f"Error creando asiento contable - {message}"
			except Exception as exc:
				frappe.log_error(message=frappe.get_traceback(), title="payroll_file_import_orchestrator")

			if not error:
				# Limpio nuevamente la temporal
				clear_temporal_data_rows(doc)

	except Exception as exe:
		error = True
		frappe.log_error(message=frappe.get_traceback(), title="payroll_file_import")
		pass

	finally:
		try:
			doc.append('import_list', {
					"status": "Failed" if error else "Completed",
					"start_date": now(),
					"result_message": message if message != "" else "Some error has occurred, check the log.",
					"finish_date": now()
				})
			doc.status = "Failed" if error else "Completed"
			doc.save(ignore_permissions=True)

		except Exception as exce:
			frappe.log_error(message=frappe.get_traceback(), title="payroll_file_import")
			pass
	return
		

def clear_temporal_data_rows(doc):

	# Limpia registros
	frappe.db.sql(f"DELETE FROM `tabQp_Payroll_Designer_Data_Temp` WHERE temporal_lot = '{doc.name}'", as_dict=1)
	frappe.db.commit()
      
def load_data_infile_to_temporal(doc):

	esc = make_esc('$ ')
	db_user = frappe.conf.db_name
	db_pass = frappe.conf.db_password
	db_name = frappe.conf.db_name

	# Buscar rutas del archivo
	abs_site_path = os.path.abspath(frappe.get_site_path())
	file_path = ''.join((abs_site_path, doc.payroll_file))

	# Load Data
	db_port = f'-P{frappe.db.port}' if frappe.db.port else ''
	db_host = esc(frappe.db.host)

	#SE REALIZA LA CARGA DE DATOS DESDE EL ARCHIVO A LA TEMPORAL A TRAVEZ DE COMMAND LINE
	load_qry = f"""<<EOF
SET @a:=0;
LOAD DATA LOCAL INFILE '{file_path}' 
INTO TABLE tabQp_Payroll_Designer_Data_Temp
CHARACTER SET latin1
LINES TERMINATED BY "\\r\\n"
(@row)
SET document_type = TRIM(SUBSTR(@row,1,2)),
document_number = TRIM(SUBSTR(@row,3,9)),
item = TRIM(SUBSTR(@row,12,3)),
date = TRIM(SUBSTR(@row,15,10)),
account = TRIM(SUBSTR(@row,25,12)),
nit = TRIM(SUBSTR(@row,37,12)),
check_number =  TRIM(SUBSTR(@row,49,10)),
debit_value =  TRIM(SUBSTR(@row,59,16)),
credit_value =  TRIM(SUBSTR(@row,75,16)),
concept = TRIM(SUBSTR(@row,91,50)),
withholding_base= TRIM(SUBSTR(@row,141,16)),
cost_center = TRIM(SUBSTR(@row,157,10)),
book = TRIM(SUBSTR(@row,167,4)),
name = CONCAT('{doc.name}_', @a:=@a+1),
temporal_lot = '{doc.name}';
EOF"""

	load_command_line = f"""mysql -h {db_host} {db_port} -u {db_user} -p{db_pass} -D {db_name} {load_qry}"""	
	load = os.system(load_command_line)

	if load != 0:
		frappe.log_error(message=load_command_line, title="payroll_file_import")

	return load

def verify_temporal_load_data(doc):

	count = frappe.db.sql(f"SELECT COUNT(*) AS count FROM `tabQp_Payroll_Designer_Data_Temp` WHERE temporal_lot = '{doc.name}'", as_dict=1)[0].count
	return count