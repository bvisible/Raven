# Base de Connaissances LM Studio + Raven

## 🚀 Architecture Hybride SDK/HTTP - NOUVELLE IMPLEMENTATION

### Mode Hybride Intelligent
Le système utilise maintenant un handler hybride qui:
1. **Détection automatique** : Teste SDK et HTTP au premier appel
2. **Cache intelligent** : Mémorise la méthode qui fonctionne (TTL 5 min)
3. **Fallback automatique** : Si SDK échoue, bascule sur HTTP
4. **Monitoring** : Fonction de status pour diagnostics

#### Fichiers de l'Architecture Hybride
- `/raven/ai/lmstudio/hybrid_handler.py` - Handler hybride principal
- `/raven/ai/lmstudio/sdk_handler.py` - Handler SDK pur
- `/raven/ai/local_llm_http_handler.py` - Handler HTTP (fallback)
- `/raven/ai/ai.py` - Point d'entrée utilisant le hybrid handler

#### Utilisation
```python
# Le système choisit automatiquement la meilleure méthode
from raven.ai.lmstudio import lmstudio_hybrid_handler
response = lmstudio_hybrid_handler(bot, message, channel_id, history)

# Pour diagnostics
from raven.ai.lmstudio import get_lmstudio_status
status = get_lmstudio_status()
# Returns: {"sdk_connected": true, "http_connected": true, "preferred_method": "SDK"}
```

## 🆕 Virtual DocType et Pending Actions - SOLUTIONS COMPLÈTES

### Architecture du Système de Pending Actions
Le système utilise un Virtual DocType (Redis-backed) pour gérer les actions qui nécessitent une confirmation utilisateur.

#### Fichiers Clés
- `/raven/raven/doctype/raven_ai_pending_action/raven_ai_pending_action.py` - Virtual DocType
- `/raven/ai/functions.py` - Fonctions exposées (create_pending_action, confirm_pending_action, etc.)

### Problèmes Résolus et Solutions

#### 1. Status Non Persistant dans Virtual DocType
**Problème**: Les changements de status n'étaient pas sauvegardés dans Redis après `db_update()`.

**Cause Racine**: Frappe cache la première valeur et ne la met pas à jour quand `set_value` est appelé avec un paramètre d'expiration.

**Solution**: Supprimer la clé avant de la mettre à jour dans `db_update()`:
```python
def db_update(self, *args, **kwargs):
    d = self.get_valid_dict(convert_dates_to_str=True)
    # ... préparer les données ...
    
    # IMPORTANT: Supprimer d'abord pour invalider le cache
    key = f"{self.REDIS_PREFIX}{d['name']}"
    frappe.cache().delete_value(key)
    
    # Maintenant sauvegarder la nouvelle valeur
    frappe.cache().set_value(key, d, expires_in_sec=expiry)
```

#### 2. TimestampMismatchError avec Virtual DocType
**Problème**: Utiliser `save()` sur un Virtual DocType cause une TimestampMismatchError.

**Solution**: Toujours utiliser `db_update()` au lieu de `save()`:
```python
# ❌ Incorrect
action.save()

# ✅ Correct
action.db_update()
```

#### 3. Longueur des Messages d'Erreur
**Problème**: `frappe.log_error` lance CharacterLengthExceededError avec des titres trop longs.

**Solution**: Ordre correct des paramètres - titre (max 140 chars), puis erreur complète:
```python
# ❌ Incorrect
frappe.log_error(str(e)[:1000], 'Execute Fallback')

# ✅ Correct
frappe.log_error('Execute Fallback', str(e))
# Ou avec limite sur le titre
frappe.log_error(f"Error: {action_id}"[:140], str(e))
```

#### 4. Loader "Thinking" Qui Reste Visible
**Problème**: Après confirmation d'action, le loader "Nora is thinking..." ne disparaît pas.

**Causes**:
1. La fonction retourne `notification_sent: True` → SDK supprime la réponse
2. Le modèle ne génère pas de message final après l'exécution

**Solutions**:
1. Ne pas inclure `notification_sent` dans le retour
2. Retourner toujours un message approprié:
```python
return {
    "status": "success",
    "message": notification_msg,
    "action_completed": True  # Pas de notification_sent
}
```
3. Instructions claires dans le prompt pour toujours fournir un message de confirmation

#### 5. Email Sans Pièce Jointe PDF
**Problème**: Les emails sont envoyés mais sans le document PDF en pièce jointe.

**Solution**: Utiliser la méthode standard Frappe avec `frappe.attach_print`:
```python
# Générer le PDF
try:
    pdf_file = frappe.attach_print(
        doctype=document_type,
        name=document_id,
        print_format=print_format
    )
    attachments = [pdf_file] if pdf_file else []
except Exception as e:
    frappe.log_error("PDF Generation Error", str(e))
    attachments = []

# Envoyer avec pièce jointe
from frappe.core.doctype.communication.email import make
make(
    doctype=document_type,
    name=document_id,
    subject=f"{document_type} {document_id}",
    content=message,
    recipients=recipient_email,
    communication_medium="Email",
    send_email=True,
    attachments=attachments,
    print_format=print_format,
    print_letterhead=True
)
```

#### 6. Processus Bloqué lors de l'Envoi d'Email
**Problème**: Le processus Frappe se bloque avec `now=True`.

**Solution**: Utiliser la file d'attente:
```python
# ❌ Bloque le processus
frappe.sendmail(..., now=True)

# ✅ Utilise la file d'attente
frappe.sendmail(..., queue="short")
```

### Best Practices pour Virtual DocType

#### Implementation
- Utiliser `db_insert()` pour créer
- Utiliser `db_update()` pour mettre à jour (avec workaround delete-first)
- Utiliser `load_from_db()` pour charger depuis Redis
- Construire manuellement le dict complet au lieu de `get_valid_dict()`

#### Gestion des Erreurs
- Toujours utiliser le bon ordre de paramètres pour `frappe.log_error`
- Wrapper try-catch pour la génération PDF
- Comportement de fallback quand les opérations échouent

#### Retours de Fonction
- Toujours retourner un dict avec `status` et `message`
- Ne pas inclure `notification_sent` si vous voulez que le SDK affiche la réponse
- Utiliser `action_completed` pour indiquer la réussite

### Séparation des Responsabilités

#### Dans Raven (Générique)
- Virtual DocType pour gérer les pending actions
- Fonctions universelles (`confirm_pending_action`, etc.)
- SDK handler sans références spécifiques business
- Prompt système générique

#### Dans Module Business (ex: neoffice-theme)
- Fonctions métier spécifiques
- Prompts détaillés pour le bot
- Instructions spécifiques (français, références business)
- Gestion des flows métier

# Base de Connaissances SDK LM Studio + Raven

## ✅ INTÉGRATION COMPLÈTE FONCTIONNELLE

### État Actuel : PRODUCTION READY v4 - HYBRID
- **Mode Hybride** : SDK prioritaire avec fallback HTTP automatique
- **Détection intelligente** : Test automatique des deux méthodes
- **Cache de connexion** : Mémorise la méthode fonctionnelle
- **Historique complet** : Messages user + assistant correctement transmis
- **Thinking sections** : Affichage HTML avec sections repliables
- **Architecture propre** : Séparation claire entre Raven (technique) et Neoffice (prompts spécifiques)
- **Monitoring** : Fonction de status pour diagnostics en temps réel

## 🔴 TOUS LES PROBLÈMES RÉSOLUS

### Résumé des Solutions Implémentées
1. **Contexte Frappe** : Restauration complète avec `frappe.init()`, `frappe.connect()`, `frappe.set_user()`
2. **Historique de Conversation** : Thread creator + messages + extraction HTML
3. **Balises Thinking** : Conversion `<|channel|>analysis<|message|>` → `<think>` fonctionnelle
4. **Méthodes SDK** : `add_assistant_response()` au lieu de `add_assistant_message()`
5. **Détection LM Studio** : Utilisation exclusive du SDK sans fallback HTTP
6. **Architecture propre** : 
   - Raven (`sdk_handler.py`) : Wrapper générique sans code spécifique
   - Raven (`functions.py`) : Fonction `confirm_pending_action` universelle
   - Neoffice (`nora_management.py`) : Prompts et instructions spécifiques à Nora

### ✅ Problème "object is not bound" - RÉSOLU
**Solution appliquée** : Restauration du contexte Frappe dans le wrapper générique avec :
```python
frappe.init(site=context['site'])
frappe.connect()
if context['user']:
    frappe.set_user(context['user'])
```

### ✅ Problème Historique de Conversation - RÉSOLU
**Symptôme** : Le bot ne se souvient pas des messages précédents
**Cause** : Les messages assistant avec balises `<think>` étaient filtrés et perdus
**Solution appliquée** : 
1. Suppression du filtrage des balises `<think>` lors de l'ajout à l'historique
2. Augmentation de la limite d'historique de 10 à 20 messages
3. Ajout de logs détaillés pour tracer l'ajout des messages
**Code corrigé** : `sdk_handler.py` lignes 440-464

## 📚 Architecture Raven

### Emplacements des Fonctions
- **Fonctions métier**: `/Users/jeremy/GitHub/neoffice-theme/neoffice_theme/ai/nora_functions.py`
- **Configuration JSON**: `/Users/jeremy/GitHub/neoffice-theme/neoffice_theme/ai/nora_functions.json`
- **Fonctions base Raven**: `/Users/jeremy/GitHub/Raven/raven/ai/functions.py`
- **Doctypes**: Configurés dans "Raven AI Function" et liés dans "Raven Bot"

### Règles Critiques
1. **AUCUNE référence directe** à neoffice_theme dans le code Raven
2. Utiliser **uniquement** les doctypes "Raven AI Function" pour la configuration
3. Import dynamique via `function_path` configuré
4. Les fonctions restent dans leurs emplacements originaux

## 🔧 SDK LM Studio

### Documentation Officielle
- Tools: https://lmstudio.ai/docs/python/agent/tools
- Act method: https://lmstudio.ai/docs/python/agent/act

### Fonctionnement du SDK
```python
# Le SDK appelle les fonctions dans ThreadPoolExecutor
# Source: /Users/jeremy/Downloads/lmstudio-python-main/src/lmstudio/json_api.py ligne 1444
pool.submit(tool_call)  # Exécute dans un thread séparé

# Validation des types avec msgspec
# Ligne 1472: parsed_kwds = convert(raw_kwds, params_struct)
```

### Exemples SDK qui fonctionnent
```python
# /Users/jeremy/Downloads/lmstudio-python-main/examples/tool-use.py
def multiply(a: float, b: float) -> float:
    """Given two numbers a and b. Returns the product of them."""
    return a * b

model.act("What is 12345 * 54321?", [multiply], on_message=chat.append)
```

## 📝 Notes sur l'Historique de Conversation

### ✅ Problème Résolu : Message initial du thread manquant
**Diagnostic** :
- Dans un thread AI, le `channel_name` est l'ID du message qui a créé le thread
- Ce message initial n'est PAS dans le channel lui-même (il est le parent)
- Requête DB normale ne retourne que les messages DANS le channel (réponses suivantes)
- Sans ce message, l'historique est incomplet

**Solution** (lignes 410-430 de ai.py) :
```python
# Récupérer le message créateur du thread
if channel.is_ai_thread and channel.channel_name:
    thread_creator_msg = frappe.get_doc("Raven Message", channel.channel_name)
    messages.append(thread_creator_msg)  # Ajouter à la liste
    
# Trier par création pour ordre correct
messages = sorted(messages, key=lambda x: x['creation'], reverse=True)
```

**Résultat** : L'historique contient maintenant TOUS les messages du thread

### ✅ Problème Résolu : Méthode Chat incorrecte
**Erreur** : `'Chat' object has no attribute 'add_assistant_message'`
**Solution** : Utiliser `chat.add_assistant_response()` au lieu de `add_assistant_message()`
- Le SDK LM Studio utilise une méthode différente pour les messages assistant
- Corrigé dans `sdk_handler.py` ligne 463

### ✅ Problème Résolu : Extraction du texte HTML
**Diagnostic** :
- Les messages bot contiennent du HTML : `<details data-summary="🧠 Nora's Thinking Process">...</details><p>20</p>`
- Les messages user contiennent aussi du HTML : `<p class="rt-Text text-sm">texte</p>`
- Le texte brut n'était pas extrait, causant la perte du contenu réel

**Solution complète** (lignes 450-477 de ai.py) :
```python
# Pour les messages bot avec thinking HTML
if "<details" in msg_text and "</details>" in msg_text:
    # Enlever la section thinking
    actual_response = re.sub(r'<details[^>]*>.*?</details>', '', msg_text, flags=re.DOTALL).strip()

# Nettoyer TOUS les tags HTML restants
if '<' in msg_text and '>' in msg_text:
    msg_text = re.sub(r'<[^>]+>', '', msg_text).strip()
    
# Pour les messages user avec paragraphes HTML  
if "<p" in msg_text and "</p>" in msg_text:
    clean_text = re.sub(r'<[^>]+>', '', msg_text).strip()
```

**Résultat** : Les messages sont maintenant du texte pur sans HTML

### ✅ Problème Résolu : Exclusion incorrecte du message actuel
**Diagnostic** :
- Messages triés en `creation desc` (plus récent en premier)
- `messages[:-1]` excluait le DERNIER (plus ancien) au lieu du PREMIER (actuel)
- L'historique perdait les anciens messages et gardait seulement l'actuel

**Solution** (ligne 443 de ai.py) :
```python
# AVANT (incorrect)
messages = list(reversed(messages[:-1] if messages else []))

# APRÈS (correct)
messages = list(reversed(messages[1:] if messages else []))
# messages[0] = message actuel (à exclure)
# messages[1:] = historique (à garder)
```

### ✅ Problème Résolu : Accès aux attributs de dictionnaires
**Erreur** : `'dict' object has no attribute 'name'`
**Solution** : Utiliser `msg.get('name')` au lieu de `msg.name` pour tous les accès
```python
# AVANT
msg.text or msg.content

# APRÈS
msg.get('text') or msg.get('content')
```

## ✅ Problème Paramètres Optionnels - RÉSOLU
**Symptôme** : Le SDK pense que tous les paramètres sont requis, même ceux marqués comme optionnels
**Erreurs** : `"Failed to parse arguments for tool create_task: Object missing required field 'assigned_to'"`
**Cause** : 
1. Le modèle envoie des chaînes vides `""` pour les paramètres optionnels
2. Le SDK interprétait tous les paramètres annotés comme requis
**Solution appliquée** :
1. **Conversion des chaînes vides en None** (lignes 105-107 de sdk_handler.py) :
   - Les chaînes vides sont converties en `None` au lieu d'être filtrées
   - Les placeholders `{{ }}` sont toujours filtrés complètement
2. **Type hints avec Optional** (lignes 175-190 de sdk_handler.py) :
   - Utilisation de `Optional[type]` pour les paramètres non-requis
   - Le SDK comprend maintenant quels paramètres sont optionnels
3. **Gestion dans create_task** (lignes 632-640 de nora_functions.py) :
   - Conversion des chaînes vides en None dans la fonction
   - Utilisation des valeurs par défaut quand None
**Résultat** : Les fonctions sont appelées correctement avec les paramètres optionnels

## ❌ Problèmes Identifiés (Historique)

### 1. Contexte Frappe Perdu
- Le SDK exécute les fonctions dans `ThreadPoolExecutor`
- Le contexte Frappe (site, user, db) n'existe pas dans le nouveau thread
- `frappe.init()` seul ne suffit pas - besoin de `frappe.connect()` pour la DB

### 2. Conversion des Paramètres
- SDK envoie: `includeDisabled` (camelCase)
- Fonction attend: `include_disabled` (snake_case)

### 3. Types de Retour
- SDK attend des strings, pas des dicts complexes
- Besoin de formatter les résultats

## ✅ Solutions Implémentées

### 1. Handler SDK Production (FONCTIONNEL)
- `/Users/jeremy/GitHub/Raven/raven/ai/lmstudio/sdk_handler.py`
- Wrapper générique avec restauration complète du contexte Frappe
- Gestion de l'historique de conversation
- Conversion des balises `<|channel|>analysis<|message|>` → `<think>`

### 2. Détection LM Studio Hybride
- Modification dans `/Users/jeremy/GitHub/Raven/raven/ai/ai.py` (lignes 509-523)
- Si `local_llm_provider == "LM Studio"` → Utilise le handler HYBRIDE
- **Fallback automatique** : SDK prioritaire, HTTP si SDK échoue
- **Cache intelligent** : Mémorise la méthode qui fonctionne
- Autres providers (Ollama, LocalAI) continuent avec HTTP handler direct

### 3. Handler HTTP (Fallback pour LM Studio)
- `/Users/jeremy/GitHub/Raven/raven/ai/local_llm_http_handler.py`
- **Sert de fallback** pour LM Studio si SDK non disponible
- **Principal** pour Ollama, LocalAI et autres providers HTTP
- Supporte les functions calls via format OpenAI et tools

## 🎯 Solution Nécessaire

### Restauration Complète du Contexte Frappe
```python
# Dans le thread du SDK, il faut:
frappe.init(site=site)  # Initialiser Frappe
frappe.connect()        # Connecter à la DB
frappe.set_user(user)   # Définir l'utilisateur

# OU utiliser frappe.utils.background_jobs patterns
```

### Alternatives à Explorer
1. **Utiliser frappe.enqueue** patterns pour gérer les threads
2. **Copier le pattern de background_jobs** de Frappe
3. **Forcer l'exécution synchrone** sans threads
4. **Utiliser le handler HTTP** qui fonctionne déjà

## 📊 Résultats des Tests

| Test | Résultat | Solution |
|------|----------|----------|
| SDK avec frappe.connect() | ✅ Fonctionne | Contexte restauré avec succès |
| Historique de conversation | ✅ Fonctionne | Messages assistant préservés intégralement |
| Balises thinking | ✅ Fonctionne | Conversion channel → think opérationnelle |
| Détection LM Studio | ✅ Fonctionne | SDK exclusif, pas de fallback HTTP |
| Appel de fonctions | ✅ Fonctionne | Wrapper générique avec contexte |

## 🔗 Références Frappe

### Gestion des Threads dans Frappe
- Background jobs: `/frappe/utils/background_jobs.py`
- Scheduler: `/frappe/utils/scheduler.py`
- DB connections: `/frappe/database.py`

### Pattern à Suivre
```python
# Comment Frappe gère les background jobs
def execute_job(site, method, event, job_name, kwargs):
    frappe.init(site=site)
    frappe.connect()
    frappe.set_user("Administrator")  # ou l'utilisateur approprié
    # Exécuter la fonction
    frappe.db.commit()
    frappe.destroy()
```

## 📝 Notes Importantes

1. **Le SDK fonctionne** - Il appelle bien les fonctions
2. **Le problème est Frappe** - Le contexte n'est pas disponible dans les threads
3. **Solution HTTP fonctionne** - Alternative viable si SDK trop complexe
4. **GPT-OSS-20B supporte les functions** - Le modèle n'est pas le problème

### ✅ Problème "manage_pending_action non appelé" - RÉSOLU v3
**Symptôme** : Le bot générait des marqueurs fictifs `<|channel|>commentary to=functions...` au lieu d'appeler la fonction
**Cause** : Architecture mélangée avec du code spécifique dans Raven
**Solution appliquée** :
1. **Nettoyage complet de `sdk_handler.py`** :
   - Suppression de toutes les fonctions spécifiques (old wrapper, manage_action wrapper)
   - Suppression de tout le français du prompt système
   - Prompt système simple axé sur l'utilisation des fonctions
2. **Fonction universelle dans `functions.py`** :
   - `confirm_pending_action()` : Handler générique pour toutes les confirmations
   - Gestion centralisée des actions en attente
3. **Instructions spécifiques dans `nora_management.py`** :
   - Prompt détaillé pour manage_pending_action
   - Exemples de flow multi-tour
   - Instructions contre les marqueurs fictifs

## 🚀 État Actuel : PRODUCTION READY v2

### ✅ Ce qui fonctionne parfaitement :
1. **SDK LM Studio** : Intégration complète avec le SDK Python (lmstudio 0.3.3)
2. **Contexte Frappe** : Restauration complète dans les threads avec `frappe.init()`, `frappe.connect()`, `frappe.set_user()`
3. **Historique Complet** : 
   - Message thread creator récupéré
   - Tous les messages du thread inclus
   - Extraction HTML correcte
   - Ordre chronologique préservé
4. **Balises Thinking** : 
   - Conversion `<|channel|>analysis<|message|>` → `<think>`
   - Affichage HTML avec `<details>` repliables
5. **Appel de fonctions** : 
   - Wrapper générique avec contexte préservé
   - Conversion camelCase → snake_case
   - Retour JSON stringifié
6. **Multi-turn Function Calling** :
   - Prompt système avec instructions explicites
   - Wrapper spécialisé pour manage_pending_action
   - Détection automatique d'actions en attente

### 🎯 Configuration Requise :
- **Raven Settings** → Local LLM Provider : "LM Studio"
- **Bot** → Model Provider : "Local LLM"
- **LM Studio** : Serveur démarré avec modèle compatible (GPT-OSS-20B recommandé)
- **URL** : Configurer dans Raven Settings (ex: nora.a.pinggy.link)

## Configuration Actuelle

- **Bot**: Nora
- **Model**: openai/gpt-oss-20b
- **Provider**: Local LLM
- **URL**: nora.a.pinggy.link
- **Site**: prod.local
- **User**: Administrator

## 📁 Structure Finale des Fichiers

### Dossier `/raven/ai/lmstudio/`
1. **`hybrid_handler.py`** - Handler hybride SDK/HTTP avec détection auto
2. **`sdk_handler.py`** - Handler SDK pur (utilisé par hybrid)
3. **`SDK_KNOWLEDGE_BASE.md`** - Cette documentation complète
4. **`__init__.py`** - Module exports (hybrid_handler, sdk_handler, status functions)

### Fichiers déplacés/renommés
- **`/raven/ai/local_llm_http_handler.py`** - Handler HTTP pour Ollama/LocalAI (PAS pour LM Studio)

### Modifications clés dans autres fichiers
- **`/raven/ai/ai.py`** :
  - Lignes 410-430 : Récupération du thread creator message
  - Lignes 509-523 : Détection LM Studio et utilisation du handler HYBRIDE
  - Lignes 443 : Exclusion correcte du message actuel `[1:]`
  - Lignes 450-477 : Extraction HTML complète
  
- **`/raven/ai/lmstudio/hybrid_handler.py`** :
  - Détection automatique SDK vs HTTP
  - Cache de méthode fonctionnelle (5 min TTL)
  - Fallback intelligent avec logs détaillés
  - Fonction de status pour monitoring

- **`/raven/ai/response_formatter.py`** :
  - Conversion des balises `<think>` en sections HTML repliables

### Fichiers supprimés (obsolètes)
- Tous les handlers de test (sdk_test.py, sdk_clean.py, etc.)
- Interceptors et wrappers divers
- Handler HTTP dans le dossier lmstudio