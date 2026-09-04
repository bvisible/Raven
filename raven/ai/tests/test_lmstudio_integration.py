#//// Neoffice - added file (no upstream equivalent). LM Studio end-to-end test (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
#//// Docstrings and comments translated from French on 2026-09-04: source files are English.
#//// The print() diagnostics below are still French, and so are the questions asked to the
#//// model - those are the fixture (a French-speaking user asking for context the prompt was
#//// supposed to carry). Note that this script cannot run as it stands: it calls
#//// EnhancedLMStudioHandler(bot=bot) and lmstudio_sdk_handler(message=..., bot=...), neither
#//// of which matches the current signatures. It wants a rewrite, not a translation.
#!/usr/bin/env python3
"""
End-to-end diagnostic against a live LM Studio server.

Checks that Nora gets its context from the prompt, i.e. without the get_current_context
function the bot used to call for it. Run by hand; it needs LM Studio up and a "Nora"
Raven Bot configured.
"""

import json
from datetime import datetime

import frappe


def test_nora_with_lmstudio():
	#//// Neoffice - English docstring (2026-09-04), see the file header.
	"""Walk the whole path: settings, bot, context variables, prompt, model, tools."""

	print("=" * 60)
	print("TEST D'INTÉGRATION: Nora + LM Studio + Context Injection")
	print("=" * 60)

	# 1. Check the configuration
	print("\n1. Vérification de la configuration...")

	# Get Raven Settings
	raven_settings = frappe.get_single("Raven Settings")
	if not hasattr(raven_settings, "local_llm_api_url") or not raven_settings.local_llm_api_url:
		print("  ❌ URL LM Studio non configurée dans Raven Settings")
		return False

	print(f"  ✓ URL LM Studio: {raven_settings.local_llm_api_url}")

	# 2. Check the Nora bot
	print("\n2. Vérification du bot Nora...")

	try:
		bot = frappe.get_doc("Raven Bot", "Nora")
		print(f"  ✓ Bot trouvé: {bot.name}")
		print(f"  - Dynamic instructions: {bot.dynamic_instructions}")
		print(f"  - Fonctions configurées: {len(bot.bot_functions) if bot.bot_functions else 0}")

		# get_current_context must not be among the configured functions any more
		has_get_context = False
		for func_link in bot.bot_functions:
			func_doc = frappe.get_doc("Raven AI Function", func_link.function)
			if func_doc.function_name == "get_current_context":
				has_get_context = True
				print("  ⚠ get_current_context est encore configuré!")
				break

		if not has_get_context:
			print("  ✓ get_current_context n'est pas dans les fonctions")

	except Exception as e:
		print(f"  ❌ Erreur lors de la récupération du bot: {e}")
		return False

	# 3. Check the context variables
	print("\n3. Test des variables de contexte...")

	from raven.ai.handler import get_variables_for_instructions

	context_vars = get_variables_for_instructions()

	print("  Variables disponibles:")
	important_vars = ["full_name", "company", "currency", "lang", "current_date"]
	for var in important_vars:
		value = context_vars.get(var, "NOT SET")  #//// Neoffice - English (2026-09-04).
		print(f"    - {var}: {value}")

	# 4. Check that the prompt renders
	print("\n4. Test du rendu du prompt...")

	if bot.dynamic_instructions:
		sample_prompt = bot.instruction[:300] if bot.instruction else ""
		rendered = frappe.render_template(sample_prompt, context_vars)

		# Every variable must have been substituted
		if "{{" in rendered:
			print("  ⚠ Variables non remplacées détectées dans le prompt")
		else:
			print("  ✓ Variables correctement remplacées")
			print(f"  Aperçu: {rendered[:150]}...")

	# 5. Talk to LM Studio
	print("\n5. Test de communication avec LM Studio...")

	try:
		from raven.ai.lmstudio import lmstudio_sdk_handler

		# Fixture: questions only the injected context can answer. French on purpose, that is
		# what the customers speak and what the model has to handle.
		test_questions = [
			"Quel est mon nom ?",
			"Dans quelle entreprise je travaille ?",
			"Quelle est la devise utilisée ?",
			"Quelle est la date d'aujourd'hui ?",
		]

		for question in test_questions:
			print(f"\n  Question: {question}")

			try:
				result = lmstudio_sdk_handler(message=question, bot=bot)

				if result.get("success"):
					response = result.get("response", "")
					print(f"  Réponse: {response[:150]}...")

					# The answer has to quote something from the context
					context_found = False
					for key in ["full_name", "company", "currency"]:
						if context_vars.get(key) and str(context_vars[key]).lower() in response.lower():
							context_found = True
							print(f"  ✓ Contexte détecté: {key} = {context_vars[key]}")
							break

					if not context_found:
						print("  ⚠ Contexte non détecté dans la réponse")
				else:
					print(f"  ❌ Erreur: {result.get('error')}")

			except Exception as e:
				print(f"  ❌ Exception: {e}")

	except ImportError as e:
		print(f"  ❌ Module LM Studio non trouvé: {e}")
		return False
	except Exception as e:
		print(f"  ❌ Erreur lors du test: {e}")
		return False

	# 6. Check the tools the handler loads
	print("\n6. Test des fonctions disponibles...")

	try:
		from raven.ai.lmstudio.enhanced_handler import EnhancedLMStudioHandler

		handler = EnhancedLMStudioHandler(bot=bot)

		print(f"  Fonctions chargées: {len(handler.tools)}")
		for tool in handler.tools[:5]:  #//// Neoffice - "first five only", English (2026-09-04).
			if hasattr(tool, "__name__"):
				print(f"    • {tool.__name__}")

		# get_current_context must not be loaded either
		tool_names = [tool.__name__ for tool in handler.tools if hasattr(tool, "__name__")]
		if "get_current_context" in tool_names:
			print("  ❌ get_current_context ne devrait pas être chargé!")
		else:
			print("  ✓ get_current_context correctement exclu")

	except Exception as e:
		print(f"  ❌ Erreur: {e}")

	print("\n" + "=" * 60)
	print("TEST TERMINÉ")
	print("=" * 60)

	return True


def test_function_calls_with_context():
	#//// Neoffice - English docstring (2026-09-04), see the file header.
	"""Check that the model still calls functions once the context is injected."""

	print("\n" + "=" * 60)
	print("TEST: Appels de fonction avec contexte")
	print("=" * 60)

	try:
		bot = frappe.get_doc("Raven Bot", "Nora")
		from raven.ai.lmstudio import lmstudio_sdk_handler

		# A request that can only be answered by calling a function, without get_current_context
		test_message = "Montre-moi la liste des produits (limite 5)"

		print(f"\nMessage: {test_message}")

		result = lmstudio_sdk_handler(message=test_message, bot=bot)

		if result.get("success"):
			print("✓ Réponse reçue")
			response = result.get("response", "")

			# Did the model call a function?
			if "FUNCTION_CALL:" in response or "get_" in response.lower():
				print("✓ Fonction détectée dans la réponse")
			else:
				print("⚠ Pas de fonction détectée")
		else:
			print(f"❌ Erreur: {result.get('error')}")

	except Exception as e:
		print(f"❌ Exception: {e}")
		import traceback

		traceback.print_exc()


def main():
	#//// Neoffice - English docstring (2026-09-04), see the file header.
	"""Entry point."""

	# Initialize Frappe
	if not frappe.db:
		frappe.init(site="prod.local")
		frappe.connect()
		frappe.set_user("Administrator")

	try:
		# Run integration test
		success = test_nora_with_lmstudio()

		# Run function call test
		test_function_calls_with_context()

		return success

	except Exception as e:
		print(f"\n❌ ERREUR FATALE: {e}")
		import traceback

		traceback.print_exc()
		return False

	finally:
		if frappe.db:
			frappe.destroy()


if __name__ == "__main__":
	import sys

	success = main()
	sys.exit(0 if success else 1)
