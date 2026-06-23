import frappe
from erpnext.projects.doctype.activity_cost.activity_cost import ActivityCost, DuplicationError
from frappe import _


class WorkingTimeActivityCost(ActivityCost):
	def set_title(self):
		super().set_title()
		if self.project:
			self.title = _("{0} ({1})").format(self.title, self.project)

	def check_unique(self):
		filters = {
			"activity_type": self.activity_type,
			"name": ("!=", self.name),
		}

		if self.employee:
			filters["employee"] = self.employee
		else:
			filters["employee"] = ("is", "not set")

		if self.project:
			filters["project"] = self.project
		else:
			filters["project"] = ("is", "not set")

		if frappe.db.exists("Activity Cost", filters):
			if self.employee:
				if self.project:
					frappe.throw(
						_(
							"Activity Cost exists for Employee {0} against Activity Type {1} and Project {2}"
						).format(self.employee, self.activity_type, self.project),
						DuplicationError,
					)
				frappe.throw(
					_("Activity Cost exists for Employee {0} against Activity Type {1}").format(
						self.employee, self.activity_type
					),
					DuplicationError,
				)

			frappe.throw(
				_("Default Activity Cost exists for Activity Type {0}").format(self.activity_type),
				DuplicationError,
			)
