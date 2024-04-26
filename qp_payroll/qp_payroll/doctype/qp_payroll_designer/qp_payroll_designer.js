// Copyright (c) 2024, Frappé and contributors
// For license information, please see license.txt

frappe.ui.form.on('Qp_Payroll_Designer', {
	refresh: function(frm) {
		if (!frm.is_new() && frm.doc.status !== "Completed") {
			frm.add_custom_button(__("Do Import"), function() {
				frappe.call({
					doc: frm.doc,
					method: "do_payroll_file",
					callback: function(r) {
						if(!r.exc) {
							if(r.message) {
								frappe.msgprint(__("El archivo esta en proceso de carga."))
							} else {
								frappe.msgprint(__("Error! Please see error log"))
							}
						}
						frm.reload_doc();
					}
				});
			});
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Reload"), function() {
				frm.reload_doc();
			});
		}
	}
});
