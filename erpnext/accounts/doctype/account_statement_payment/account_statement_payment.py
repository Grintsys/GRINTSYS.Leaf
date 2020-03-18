# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta, date

class AccountStatementPayment(Document):
		
	def validate(self):
		total_price = self.sum_total()
		self.total	= total_price	

	def on_update(self):
		doc = frappe.get_doc("Patient statement", self.patient_statement)
		doc.save()	
	
	def sum_total(self):
		total_price = 0
		requisitions = frappe.get_all("Inventory Requisition", ["name"], filters = {"patient_statement": self.patient_statement, "docstatus": 1})

		for req in requisitions:
			products = frappe.get_all("Inventory Item", ["item", "product_name", "quantity"], filters = {"parent": req.name})

			for item in products:
				product_price = frappe.get_all("Item Price", ["price_list_rate"], filters = {"item_code": item.item})

				for price in product_price:
					total_price += req.quantity * price.price_list_rate
		
		devrequisitions = requisitions = frappe.get_all("Return of inventory requisition", ["name"], filters = {"patient_statement": self.patient_statement, "docstatus": 1})

		for devr in devrequisitions:
			products = frappe.get_all("Inventory Item", ["item", "product_name", "quantity"], filters = {"parent": devr.name})

			for item in products:
				product_price = frappe.get_all("Item Price", ["price_list_rate"], filters = {"item_code": item.item})

				for price in product_price:
					total_price -= devr.quantity * price.price_list_rate
	
	return total_price

