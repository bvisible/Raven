from typing import Any, Dict, List, Optional, Union, Callable
import frappe
import json
import inspect

try:
    from agents import FunctionTool
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    frappe.log_error("OpenAI Agents SDK not installed. Run 'pip install openai-agents'")


def create_raven_tools(bot) -> List[FunctionTool]:
    """
    Create function tools for Raven bot
    
    Args:
        bot: Raven bot document
        
    Returns:
        List[FunctionTool]: List of function tools
    """
    tools = []
    
    # Get the bot functions
    if hasattr(bot, "functions") and bot.functions:
        for func in bot.functions:
            # Get function details from Raven Bot Functions
            function_doc = frappe.get_doc("Raven Bot Functions", func.function)
            
            # Create a function tool for this function
            if function_doc:
                tool = create_function_tool(
                    function_doc.name,
                    function_doc.description,
                    function_doc.function_name,
                    function_doc.get_params()
                )
                tools.append(tool)
    
    return tools


def create_function_tool(
    name: str, 
    description: str, 
    function_name: str, 
    parameters: Dict[str, Any]
) -> FunctionTool:
    """
    Create a FunctionTool for Raven functions
    
    Args:
        name: Tool name
        description: Tool description
        function_name: Function name to call
        parameters: Function parameters schema
        
    Returns:
        FunctionTool: Function tool
    """
    # Get the actual function to call
    function = get_function_from_name(function_name)
    
    if not function:
        frappe.log_error(f"Function {function_name} not found")
        return None
    
    # Create FunctionTool
    tool = FunctionTool(
        function=function,
        name=name,
        description=description,
        parameter_schema=parameters
    )
    
    return tool


def get_function_from_name(function_name: str) -> Callable:
    """
    Get a function from its name
    
    Args:
        function_name: Fully qualified function name (module.function)
        
    Returns:
        Callable: Function
    """
    try:
        # Split module and function
        module_name, func_name = function_name.rsplit(".", 1)
        
        # Import module
        module = __import__(module_name, fromlist=[func_name])
        
        # Get function
        function = getattr(module, func_name)
        
        return function
    except (ValueError, ImportError, AttributeError) as e:
        frappe.log_error(f"Error getting function {function_name}: {e}")
        return None


# Function wrapper to adapt Frappe functions to Agents SDK
def wrap_frappe_function(func: Callable) -> Callable:
    """
    Wrap a Frappe function to handle exceptions
    
    Args:
        func: Function to wrap
        
    Returns:
        Callable: Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Convert Frappe document to dictionary if needed
            if hasattr(result, "as_dict"):
                result = result.as_dict()
                
            # If result is a list of Frappe documents, convert each to dictionary
            elif isinstance(result, list) and result and hasattr(result[0], "as_dict"):
                result = [item.as_dict() if hasattr(item, "as_dict") else item for item in result]
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            frappe.log_error(f"Error in function {func.__name__}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Copy function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    wrapper.__signature__ = inspect.signature(func)
    
    return wrapper


# Standard CRUD function generators
def create_get_function(doctype: str) -> Callable:
    """
    Create a get function for a doctype
    
    Args:
        doctype: DocType name
        
    Returns:
        Callable: Function to get a document
    """
    def get_doc(name: str, **kwargs):
        """
        Get a document
        
        Args:
            name: Name of the document
            
        Returns:
            dict: Document data
        """
        doc = frappe.get_doc(doctype, name)
        return doc
    
    get_doc.__name__ = f"get_{doctype.lower().replace(' ', '_')}"
    get_doc.__doc__ = f"Get a {doctype} document"
    
    return wrap_frappe_function(get_doc)


def create_create_function(doctype: str) -> Callable:
    """
    Create a function to create a document
    
    Args:
        doctype: DocType name
        
    Returns:
        Callable: Function to create a document
    """
    def create_doc(**kwargs):
        """
        Create a document
        
        Args:
            **kwargs: Document fields
            
        Returns:
            dict: Created document
        """
        doc = frappe.get_doc({
            "doctype": doctype,
            **kwargs
        })
        doc.insert()
        return doc
    
    create_doc.__name__ = f"create_{doctype.lower().replace(' ', '_')}"
    create_doc.__doc__ = f"Create a {doctype} document"
    
    return wrap_frappe_function(create_doc)


def create_update_function(doctype: str) -> Callable:
    """
    Create a function to update a document
    
    Args:
        doctype: DocType name
        
    Returns:
        Callable: Function to update a document
    """
    def update_doc(name: str, **kwargs):
        """
        Update a document
        
        Args:
            name: Name of the document
            **kwargs: Fields to update
            
        Returns:
            dict: Updated document
        """
        doc = frappe.get_doc(doctype, name)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        
        doc.save()
        return doc
    
    update_doc.__name__ = f"update_{doctype.lower().replace(' ', '_')}"
    update_doc.__doc__ = f"Update a {doctype} document"
    
    return wrap_frappe_function(update_doc)


def create_delete_function(doctype: str) -> Callable:
    """
    Create a function to delete a document
    
    Args:
        doctype: DocType name
        
    Returns:
        Callable: Function to delete a document
    """
    def delete_doc(name: str):
        """
        Delete a document
        
        Args:
            name: Name of the document
            
        Returns:
            dict: Result of deletion
        """
        frappe.delete_doc(doctype, name)
        return {"message": f"{doctype} {name} deleted successfully"}
    
    delete_doc.__name__ = f"delete_{doctype.lower().replace(' ', '_')}"
    delete_doc.__doc__ = f"Delete a {doctype} document"
    
    return wrap_frappe_function(delete_doc)


def create_list_function(doctype: str) -> Callable:
    """
    Create a function to list documents
    
    Args:
        doctype: DocType name
        
    Returns:
        Callable: Function to list documents
    """
    def list_docs(filters: dict = None, fields: list = None, limit: int = 100, order_by: str = "modified desc"):
        """
        List documents
        
        Args:
            filters: Filters to apply
            fields: Fields to return
            limit: Maximum number of documents to return
            order_by: Order by clause
            
        Returns:
            list: List of documents
        """
        if not fields:
            fields = ["name", "modified"]
            
        result = frappe.get_all(
            doctype,
            filters=filters,
            fields=fields,
            limit_page_length=limit,
            order_by=order_by
        )
        
        return result
    
    list_docs.__name__ = f"list_{doctype.lower().replace(' ', '_')}"
    list_docs.__doc__ = f"List {doctype} documents"
    
    return wrap_frappe_function(list_docs)