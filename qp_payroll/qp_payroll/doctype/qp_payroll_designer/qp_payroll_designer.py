# Copyright (c) 2024, Frappé and contributors
# For license information, please see license.txt

import frappe
import os
from frappe import _
from frappe.model.document import Document
from qp_payroll.qp_payroll.personalization.payroll_file_import import payroll_file_import


class Qp_Payroll_Designer(Document):
	
	def validate(self):
		
		print(self)

		if not self.payroll_file:
			frappe.throw(_("Please attach file to import")) 
		
	@frappe.whitelist()
	def do_payroll_file(self):

		try:
			result_import = self.do_import()
			return True

		except Exception as error:
			frappe.log_error(message=frappe.get_traceback(), title="do_payroll_file")
			pass

		return False
	
	def do_import(self):

		# Validar que haya un adjunto
		if not self.payroll_file:
			frappe.throw(_("Please attach file to import"))

		# Validar la extensión del archivo
		root, extension = os.path.splitext(self.payroll_file)

		if extension != ".txt":
			frappe.throw(_("Allowed extension .txt"))

		if self.status == 'Active':
			frappe.throw(_("Job already running to upload."))
		
		self.status = 'Active'
		self.save(ignore_permissions=True)
		self.reload()

		frappe.enqueue(payroll_file_import, doc=self, is_async=True, timeout=54000)

		return