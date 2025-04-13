import { RavenBotFunctions } from '../RavenAI/RavenBotFunctions'

export interface RavenBot{
	creation: string
	name: string
	modified: string
	owner: string
	modified_by: string
	docstatus: 0 | 1 | 2
	parent?: string
	parentfield?: string
	parenttype?: string
	idx?: number
	/**	Bot Name : Data	*/
	bot_name: string
	/**	Image : Attach Image	*/
	image?: string
	/**	Raven User : Link - Raven User	*/
	raven_user?: string
	/**	Description : Small Text	*/
	description?: string
	/**	Is Standard : Check	*/
	is_standard?: 0 | 1
	/**	Module : Link - Module Def	*/
	module?: string
	/**	Is AI Bot? : Check	*/
	is_ai_bot?: 0 | 1
	/**	Debug Mode : Check - If enabled, stack traces of errors will be sent as messages by the bot 	*/
	debug_mode?: 0 | 1
	/**	Model Provider : Select - Select the model provider for this bot	*/
	model_provider?: "OpenAI" | "LM Studio" | "Ollama" | "LocalAI"
	/**	Model Name : Data - The name of the model to use	*/
	model_name?: string
	/**	Vector Store IDs : Small Text - Comma-separated list of OpenAI vector store IDs to search in	*/
	vector_store_ids?: string
	/**	Enable Local RAG : Check - Enable to use local RAG implementation instead of OpenAI's file search	*/
	enable_local_rag?: 0 | 1
	/**	Local RAG Provider : Select - The vector store provider to use for local RAG	*/
	local_rag_provider?: "Chroma" | "FAISS" | "Weaviate"
	/**	Agent Settings : JSON - JSON configuration for the agent (temperature, top_p, etc.)	*/
	agent_settings?: string
	/**	OpenAI Assistant ID (Legacy) : Data	*/
	openai_assistant_id?: string
	/**	Enable Code Interpreter : Check - Enable this if you want the bot to be able to process data files and execute code to analyze them.	*/
	enable_code_interpreter?: 0 | 1
	/**	Allow Bot to Write Documents : Check	*/
	allow_bot_to_write_documents?: 0 | 1
	/**	Enable File Search : Check - Enable this if you want the bot to be able to read PDF files and other documents.

File search enables the agent with knowledge from files that you upload, allowing it to answer questions based on document content.	*/
	enable_file_search?: 0 | 1
	/**	Instruction : Long Text - You can use Jinja variables here to customize the instruction to the bot at run time if dynamic instructions are enabled.	*/
	instruction?: string
	/**	Dynamic Instructions : Check - Dynamic Instructions allow you to embed Jinja tags in your instruction to the bot. Hence the instruction would be different based on the user who is calling the bot or the data in your system. These instructions are computed every time the bot is called. Check this if you want to embed things like Employee ID, Company Name etc in your instructions dynamically	*/
	dynamic_instructions?: 0 | 1
	/**	Bot Functions : Table - Raven Bot Functions	*/
	bot_functions?: RavenBotFunctions[]
}