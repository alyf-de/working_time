import frappe
from erpnext.projects.doctype.activity_cost.activity_cost import DuplicationError
from frappe.tests.utils import FrappeTestCase


class TestWorkingTimeActivityCost(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.activity_type = "Default"
		if not frappe.db.exists("Activity Type", cls.activity_type):
			frappe.get_doc({"doctype": "Activity Type", "activity_type": cls.activity_type}).insert(
				ignore_permissions=True
			)

		cls.company = frappe.db.get_value("Company", {}, "name")
		cls.employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		if not cls.employee:
			employee = frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": "Working Time",
					"last_name": "Test",
					"company": cls.company,
					"gender": "Male",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2020-01-01",
				}
			)
			employee.insert(ignore_permissions=True)
			cls.employee = employee.name

		cls.project_a = cls._ensure_project("WT Test Project A")
		cls.project_b = cls._ensure_project("WT Test Project B")

	@classmethod
	def _ensure_project(cls, project_name):
		if frappe.db.exists("Project", {"project_name": project_name}):
			return frappe.db.get_value("Project", {"project_name": project_name}, "name")

		project = frappe.get_doc({"doctype": "Project", "project_name": project_name})
		project.insert(ignore_permissions=True)
		return project.name

	def setUp(self):
		frappe.db.delete(
			"Activity Cost",
			{"employee": self.employee, "activity_type": self.activity_type},
		)

	def tearDown(self):
		frappe.db.delete(
			"Activity Cost",
			{"employee": self.employee, "activity_type": self.activity_type},
		)

	def _make_activity_cost(self, project=None):
		return frappe.get_doc(
			{
				"doctype": "Activity Cost",
				"employee": self.employee,
				"activity_type": self.activity_type,
				"project": project,
				"billing_rate": 100,
				"costing_rate": 50,
			}
		)

	def test_different_projects_allowed(self):
		self._make_activity_cost(project=self.project_a).insert()
		self._make_activity_cost(project=self.project_b).insert()
		self._make_activity_cost().insert()

	def test_duplicate_without_project_rejected(self):
		self._make_activity_cost().insert()
		duplicate = self._make_activity_cost()
		self.assertRaises(DuplicationError, duplicate.insert)

	def test_duplicate_with_same_project_rejected(self):
		self._make_activity_cost(project=self.project_a).insert()
		duplicate = self._make_activity_cost(project=self.project_a)
		self.assertRaises(DuplicationError, duplicate.insert)
