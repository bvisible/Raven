"""
Raven AI Test Suite
Modular testing framework for Raven AI system
"""

from .test_actresult import ActResultTests
from .test_conversation import ConversationTests
# //// Neoffice — test_functions.py was never committed (only described in ai.md), and
# //// frappe's test runner imports every test module of the app: this package-level
# //// import killed `bench run-tests --app raven` before any test ran (CI, 2026-09-03).
try:
    from .test_functions import FunctionTests
except ImportError:  # module absent from the repository
    FunctionTests = None
from .test_integration import IntegrationTests
from .test_lmstudio import LMStudioTests
from .test_modules import ModuleTests
from .test_openai import OpenAITests
from .test_runner import run_all_tests, run_test_category

__all__ = [
	"ModuleTests",
	"LMStudioTests",
	"OpenAITests",
	"FunctionTests",
	"IntegrationTests",
	"ActResultTests",
	"ConversationTests",
	"run_all_tests",
	"run_test_category",
]
