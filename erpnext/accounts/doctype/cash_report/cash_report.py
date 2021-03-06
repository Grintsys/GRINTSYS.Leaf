# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import date
from frappe.model.document import Document

class CashReport(Document):
	def validate(self):
		self.calculate_totals()
	
	def calculate_totals(self):
		sales_invoice = frappe.get_all("Sales Invoice", ["exonerated", "grand_total", "total", "numeration", "total_taxes_and_charges", "name", "taxes_and_charges"], filters = {"is_pos": 0, "company": self.company, "due_date": self.billing_date, "pos": self.pos, "type_document": self.document_type, "docstatus": 1})
		#sales_cards = frappe.get_all("Sales Invoice", ["total"], filters = {"is_pos": 1, "company": self.company, "due_date": self.billing_date, "pos": self.pos, "type_document": self.document_type, "docstatus": 1})
		
		#variables general data
		create_date = date.today()
		rtn = "0502199804256"
		billing_series = ""
		initial_document = ""
		final_document = ""

		#variables taxes
		taxed15 = 0
		taxed18 = 0
		exempt = 0
		exonerated = 0
		isv_taxed15 = 0
		isv_taxed18 = 0
		isv_exempt = 0
		isv_exonerated = 0

		#variables details total
		total_base_isv15 = 0
		total_base_isv18 = 0
		total_exempt = 0
		total_isv15 = 0
		total_isv18 = 0
		grand_total = 0

		mode_pay = frappe.get_all("Mode of Payment", ["name"])

		payments_entry = frappe.get_all("Payment Entry", ["paid_amount"], filters = {"posting_date": self.billing_date, "docstatus": 1})
		
		arrmode = []

		registers_total = frappe.get_all("Details totals proof of daily sales", ["name", "mode_of_payment"], filters = {"parent": self.name})
		
		if len(registers_total) > 0:
			for reg in registers_total:
				frappe.delete_doc("Details totals proof of daily sales", reg.name)

		if len(sales_invoice) > 0 or  len(payments_entry) > 0:

			if len(sales_invoice) > 0:
				billing_series = sales_invoice[0].numeration[0:10]
				final_document = sales_invoice[0].numeration[11:19]

			total_credit = 0

			for sales in sales_invoice:
				initial_document = sales.numeration[11:19]
				sale_total = 0
				for mode in mode_pay:
					total_payment = 0
					payments_entry = frappe.get_all("Payment Entry", ["name", "paid_amount"], filters = {"posting_date": self.billing_date, "mode_of_payment": mode.name, "docstatus": 1})
					
					for payment in payments_entry:
						references = frappe.get_all("Payment Entry Reference", filters = {"reference_name": sales.name, "parent": payment.name})

						if len(references) > 0:
							total_payment += payment.paid_amount							
						
					grand_total += total_payment			

					if len(arrmode) > 0:
						cont = 0
						for arr in arrmode:
							cont += 1
							if arr[0] == mode.name:
								arr[1] += total_payment
								cont -= 1
							
							if cont == len(arrmode):
								pay = [mode.name, total_payment]
								arrmode.append(pay)
								break
					else:
						pay = [mode.name, total_payment]
						arrmode.append(pay)

					sale_total += total_payment
				
				if sale_total < sales.grand_total:
					total_credit += sales.grand_total - sale_total
				
								
				if sales.taxes_and_charges:
					if sales.exonerated == 1:
						exonerated += sales.total
					else:
						invoice_table_taxes = frappe.get_all("Sales Taxes and Charges", ["name", "rate", "tax_amount"], filters = {"parent": sales.name})

						for invoice_tax in invoice_table_taxes:

							if invoice_tax.rate == 15:
								taxed15 += sales.total							
							
							if invoice_tax.rate == 18:
								taxed18 += sales.total
				else:
					items = frappe.get_all("Sales Invoice Item", ["item_code", "amount"], filters = {"parent": sales.name})

					for item in items:
						item_taxes = frappe.get_all("Item Tax", ['name', "item_tax_template"], filters = {"parent": item.item_code})
						if len(item_taxes) >0:
							for item_tax in item_taxes:
								tax_tamplates = frappe.get_all("Item Tax Template", ["name"], filters = {"name": item_tax.item_tax_template})
							
								for tax_tamplate in tax_tamplates:

									tax_details = frappe.get_all("Item Tax Template Detail", ["name", "tax_rate"], filters = {"parent": tax_tamplate.name})
								
									for tax_detail in tax_details:

										if tax_detail.tax_rate == 15:
											if sales.exonerated == 1:
												exonerated += item.amount
											else:
												taxed15 += item.amount
								
										if tax_detail.tax_rate == 18:
											if sales.exonerated == 1:
												exonerated += item.amount
											else:
												taxed18 += item.amount
						else:
							exempt += item.amount
			
			for ar in arrmode:
				row = self.append("totals_table", {})
				row.mode_of_payment = ar[0]
				row.total = ar[1]

			grand_total += total_credit	

			credit_register = frappe.get_all("Details totals proof of daily sales", ["name"], filters = {"mode_of_payment": "Credit", "parent": self.name})

			if len(credit_register) > 0:
				doccredit = frappe.get_doc("Details totals proof of daily sales", credit_register[0].name)
				doccredit.total = total_credit
				doccredit.save()
			else:
				rowcredit = self.append("totals_table", {})
				rowcredit.mode_of_payment = "Credit"
				rowcredit.total = total_credit
		
		total_other_pay = 0
		payments_entry = frappe.get_all("Payment Entry", ["name", "paid_amount"], filters = {"posting_date": self.billing_date, "docstatus": 1})

		for pay_r in payments_entry:
			references = frappe.get_all("Payment Entry Reference", ["reference_name"], filters = {"parent": pay_r.name})
			
			for ref in references:
				sales_invoice = frappe.get_all("Sales Invoice", ["posting_date"], filters = {"name": ref.reference_name})
				
				for sa_in in sales_invoice:
					if str(sa_in.posting_date) < str(self.billing_date):
						total_other_pay += pay_r.paid_amount
		
		other_register = frappe.get_all("Details totals proof of daily sales", ["name"], filters = {"mode_of_payment": "Other Payments", "parent": self.name})

		if len(other_register) > 0:
			docother = frappe.get_doc("Details totals proof of daily sales", other_register[0].name)
			docother.total = total_other_pay
			docother.save()
		else:
			rowother= self.append("totals_table", {})
			rowother.mode_of_payment = "Other Payments"
			rowother.total = total_other_pay
		
		grand_total += total_other_pay

		isv_taxed15 += taxed15 * (15/100)
		isv_taxed18 += taxed18 * (18/100)
		# total_taxes = taxed15 + taxed18 + isv_taxed15 + isv_taxed18
		# exempt = grand_total - total_taxes
		
		self.create_date = create_date
		self.rtn = rtn
		self.billing_series = billing_series
		self.initial_document = initial_document
		self.final_document = final_document

		self.taxed15 = taxed15
		self.taxed18 = taxed18
		self.exempt = exempt
		self.exonerated = exonerated
		self.isv_taxed15 = isv_taxed15
		self.isv_taxed18 = isv_taxed18
		self.isv_exempt = isv_exempt
		self.isv_exonerated = isv_exonerated

		self.total_base_isv15 = taxed15
		self.total_base_isv18 = taxed18
		self.total_exempt = exempt
		self.total_isv15 = isv_taxed15
		self.total_isv18 = isv_taxed18
		self.total_exonerated = exonerated
		self.grand_total = grand_total