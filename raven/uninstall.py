import frappe

def after_uninstall():
    remove_standard_navbar_items()


def remove_standard_navbar_items():
    
    frappe.db.delete("Navbar Item", {"item_label": "Raven", "is_standard": 1, "item_type": "Route", "route": "/raven"})
    frappe.db.commit()