"""
ADRI Problem Demonstration Data - Reusable GitHub Issue Scenarios

This module provides realistic data scenarios based on documented GitHub issues
from AI frameworks, demonstrating the specific problems ADRI solves.

Each scenario includes:
- Good data that should work normally
- Bad data that causes the documented GitHub issues
- Clear mapping to real GitHub issue numbers
- Business impact context for AI Agent Engineers
"""

from typing import Any, Dict, List


class AutoGenProblems:
    """AutoGen-specific problem scenarios based on 54+ documented GitHub issues."""

    # Issue #6819: "Conversational flow is not working as expected"
    CONVERSATION_FLOW_GOOD = {
        "research_topic": "AI in Healthcare Research",
        "conversation_type": "research_collaboration",
        "participants": ["researcher", "data_analyst", "report_writer"],
        "message_format": "structured",
        "conversation_id": "conv_research_001",
        "initial_message": "Let's conduct comprehensive research on AI applications in healthcare",
        "expected_rounds": 5,
        "termination_condition": "research_complete",
    }

    CONVERSATION_FLOW_BAD = {
        "research_topic": "",  # Empty topic breaks conversation flow
        "conversation_type": None,  # Missing type confuses agents
        "participants": [],  # No participants breaks multi-agent chat
        "message_format": "invalid_format",  # Unknown format causes parsing failures
        "conversation_id": 12345,  # Should be string, not int
        "initial_message": None,  # Missing message stops conversation start
        "expected_rounds": -1,  # Invalid round count
        "termination_condition": "",  # Empty condition prevents proper ending
    }

    # Issue #5736: "Function Arguments as Pydantic Models or Dataclasses Fail"
    FUNCTION_CALL_GOOD = {
        "function_name": "analyze_research_data",
        "arguments": {
            "data_source": "pubmed_abstracts",
            "analysis_type": "sentiment_analysis",
            "sample_size": 1000,
            "confidence_threshold": 0.85,
            "output_format": "json",
        },
        "caller_agent": "data_analyst",
        "expected_return_type": "analysis_result",
    }

    FUNCTION_CALL_BAD = {
        "function_name": None,  # Missing function name breaks tool calls
        "arguments": "invalid_string",  # Should be dict, not string
        "caller_agent": "",  # Empty agent name confuses routing
        "expected_return_type": 12345,  # Should be string, not int
    }

    # Issue #6123: "Re-evaluating Internal Message Handling"
    MESSAGE_HANDLING_GOOD = {
        "message_id": "msg_001",
        "sender": "researcher",
        "recipient": "data_analyst",
        "content": "Please analyze these research findings for statistical significance",
        "timestamp": "2024-01-15T10:30:00Z",
        "message_type": "research_request",
        "attachments": ["research_data.json"],
        "priority": "high",
        "conversation_context": "healthcare_ai_research",
    }

    MESSAGE_HANDLING_BAD = {
        "message_id": "",  # Empty ID breaks message tracking
        "sender": None,  # Missing sender confuses routing
        "recipient": "",  # Empty recipient breaks delivery
        "content": "",  # Empty content provides nothing to process
        "timestamp": "invalid-date",  # Malformed timestamp breaks chronology
        "message_type": 12345,  # Should be string, not int
        "attachments": "not_a_list",  # Should be list, not string
        "priority": "invalid_priority",  # Unknown priority level
        "conversation_context": None,  # Missing context loses conversation thread
    }


class LangChainProblems:
    """LangChain-specific problem scenarios based on 525+ documented GitHub issues."""

    # Issue pattern: Chain input validation failures
    CHAIN_INPUT_GOOD = {
        "customer_query": "I need help with my account billing issue",
        "customer_id": "CUST_12345",
        "interaction_type": "billing_support",
        "priority": "medium",
        "previous_context": "Account setup completed last week",
        "agent_capabilities": ["billing", "account_management"],
        "response_tone": "helpful_professional",
    }

    CHAIN_INPUT_BAD = {
        "customer_query": "",  # Empty query breaks chain processing
        "customer_id": None,  # Missing ID prevents customer lookup
        "interaction_type": "unknown_type",  # Invalid type confuses routing
        "priority": 999,  # Should be string, not int
        "previous_context": None,  # Missing context loses conversation state
        "agent_capabilities": "not_a_list",  # Should be list, not string
        "response_tone": "",  # Empty tone provides no guidance
    }

    # Issue pattern: Memory and context management failures
    MEMORY_CONTEXT_GOOD = {
        "conversation_id": "conv_billing_001",
        "customer_history": [
            {"date": "2024-01-10", "issue": "account_setup", "resolved": True},
            {"date": "2024-01-15", "issue": "billing_question", "resolved": False},
        ],
        "current_session": {
            "start_time": "2024-01-15T14:30:00Z",
            "messages": 3,
            "sentiment": "neutral",
        },
        "context_window": 10,
        "memory_type": "conversation_buffer",
    }

    MEMORY_CONTEXT_BAD = {
        "conversation_id": "",  # Empty ID breaks context tracking
        "customer_history": "invalid_format",  # Should be list, not string
        "current_session": None,  # Missing session info loses state
        "context_window": -5,  # Invalid negative window
        "memory_type": "unknown_type",  # Invalid memory type breaks processing
    }


class CrewAIProblems:
    """CrewAI-specific problem scenarios based on documented GitHub issues."""

    # Issue pattern: Crew coordination and task distribution failures
    CREW_COORDINATION_GOOD = {
        "crew_name": "Market Analysis Team",
        "mission": "Analyze quarterly market trends for Q4 2024",
        "agents": [
            {"role": "market_researcher", "goal": "Gather market data"},
            {"role": "data_analyst", "goal": "Analyze trends and patterns"},
            {"role": "report_writer", "goal": "Create executive summary"},
        ],
        "tasks": [
            {
                "id": "task_001",
                "description": "Collect Q4 market data",
                "assigned_to": "market_researcher",
            },
            {
                "id": "task_002",
                "description": "Analyze data trends",
                "assigned_to": "data_analyst",
            },
            {
                "id": "task_003",
                "description": "Write executive report",
                "assigned_to": "report_writer",
            },
        ],
        "coordination_mode": "sequential",
        "expected_deliverable": "quarterly_market_report",
    }

    CREW_COORDINATION_BAD = {
        "crew_name": "",  # Empty name breaks crew identification
        "mission": None,  # Missing mission provides no direction
        "agents": [],  # Empty agents list breaks crew formation
        "tasks": "not_a_list",  # Should be list, not string
        "coordination_mode": "invalid_mode",  # Unknown mode breaks coordination
        "expected_deliverable": "",  # Empty deliverable provides no target
    }

    # Issue pattern: Agent role and capability mismatches
    AGENT_ROLES_GOOD = {
        "agent_id": "agent_researcher_001",
        "role": "market_researcher",
        "capabilities": ["data_collection", "market_analysis", "trend_identification"],
        "tools": ["web_search", "data_scraper", "analytics_api"],
        "experience_level": "senior",
        "specialization": "technology_markets",
        "collaboration_style": "data_driven",
    }

    AGENT_ROLES_BAD = {
        "agent_id": "",  # Empty ID breaks agent identification
        "role": None,  # Missing role confuses task assignment
        "capabilities": "invalid_format",  # Should be list, not string
        "tools": [],  # Empty tools list limits functionality
        "experience_level": "unknown_level",  # Invalid level breaks matching
        "specialization": "",  # Empty specialization reduces effectiveness
        "collaboration_style": 12345,  # Should be string, not int
    }


class LlamaIndexProblems:
    """LlamaIndex-specific problem scenarios based on 949+ documented GitHub issues."""

    # Issue #19696: "After multiple operations on the index file, docstore.json will not be a complete JSON"
    DOCUMENT_INGESTION_GOOD = {
        "batch_id": "batch_knowledge_001",
        "documents": [
            {
                "doc_id": "doc_001",
                "content": "ADRI provides comprehensive data quality validation for enterprise AI systems.",
                "metadata": {
                    "source": "knowledge_base",
                    "category": "technical_documentation",
                    "author": "AI Team",
                    "last_updated": "2024-01-15T10:30:00Z",
                    "word_count": 145,
                },
            }
        ],
        "pipeline_config": "enterprise_ingestion",
        "quality_checks": True,
        "chunk_size": 512,
        "overlap": 50,
    }

    DOCUMENT_INGESTION_BAD = {
        "batch_id": "",  # Empty batch ID breaks ingestion tracking
        "documents": [],  # Empty documents list fails ingestion
        "pipeline_config": None,  # Missing config breaks processing pipeline
        "quality_checks": "invalid",  # Should be boolean, not string
        "chunk_size": -100,  # Invalid negative chunk size
        "overlap": "invalid_overlap",  # Should be int, not string
    }

    # Issue #19508: "Retrieving data from SupabaseVectorStore returns 'Empty response'"
    VECTOR_QUERY_GOOD = {
        "query_text": "How does ADRI improve data quality in AI systems?",
        "similarity_threshold": 0.75,
        "max_results": 5,
        "embedding_model": "text-embedding-ada-002",
        "search_mode": "semantic",
        "filters": {"category": "technical_documentation", "confidence_min": 0.8},
        "response_format": "detailed",
    }

    VECTOR_QUERY_BAD = {
        "query_text": "",  # Empty query breaks vector search
        "similarity_threshold": 1.5,  # Invalid threshold > 1.0
        "max_results": -1,  # Invalid negative result count
        "embedding_model": None,  # Missing model breaks embeddings
        "search_mode": "unknown_mode",  # Invalid mode confuses retrieval
        "filters": "not_a_dict",  # Should be dict, not string
        "response_format": "",  # Empty format provides no guidance
    }

    # Issue #19387: "Node deserialization fails when store_text is false"
    NODE_SERIALIZATION_GOOD = {
        "node_id": "node_tech_001",
        "text_content": "Data quality validation prevents AI system failures through multi-dimensional assessment.",
        "metadata": {
            "source_document": "adri_technical_guide.pdf",
            "page_number": 15,
            "section": "quality_dimensions",
            "extraction_confidence": 0.95,
        },
        "embedding": [0.1, 0.2, 0.3],  # Sample embedding vector
        "store_text": True,
        "node_type": "document_chunk",
    }

    NODE_SERIALIZATION_BAD = {
        "node_id": None,  # Missing node ID breaks serialization
        "text_content": "",  # Empty content loses information
        "metadata": "invalid_metadata",  # Should be dict, not string
        "embedding": "not_a_vector",  # Should be list, not string
        "store_text": "invalid_boolean",  # Should be boolean, not string
        "node_type": "",  # Empty type confuses deserialization
    }


class HaystackProblems:
    """Haystack-specific problem scenarios based on 347+ documented GitHub issues."""

    # Document processing pipeline failures (89+ issues)
    DOCUMENT_PROCESSING_GOOD = {
        "pipeline_id": "doc_pipeline_001",
        "documents": [
            {
                "content": "ADRI ensures reliable document processing in knowledge management systems.",
                "meta": {
                    "source": "enterprise_knowledge_base",
                    "document_type": "technical_documentation",
                    "encoding": "utf-8",
                    "language": "english",
                    "confidence": 0.95,
                },
            }
        ],
        "preprocessing_config": {
            "clean_text": True,
            "split_by": "sentence",
            "max_length": 1000,
        },
        "batch_size": 32,
        "error_handling": "graceful",
    }

    DOCUMENT_PROCESSING_BAD = {
        "pipeline_id": "",  # Empty pipeline ID breaks tracking
        "documents": [],  # Empty documents list fails processing
        "preprocessing_config": None,  # Missing config breaks pipeline
        "batch_size": -5,  # Invalid negative batch size
        "error_handling": "unknown_mode",  # Invalid error handling mode
    }

    # Retrieval quality problems (134+ issues)
    SEARCH_RETRIEVAL_GOOD = {
        "query": "How does ADRI improve search quality in knowledge systems?",
        "retriever_config": {
            "top_k": 10,
            "similarity_threshold": 0.7,
            "retrieval_mode": "hybrid",
            "boost_factor": 1.2,
        },
        "filters": {
            "document_type": ["technical", "reference"],
            "language": "english",
            "confidence_min": 0.8,
        },
        "result_format": "detailed",
    }

    SEARCH_RETRIEVAL_BAD = {
        "query": "",  # Empty query breaks retrieval
        "retriever_config": "invalid_format",  # Should be dict, not string
        "filters": None,  # Missing filters breaks filtering
        "result_format": "unknown_format",  # Invalid result format
    }

    # Component integration failures (67+ issues)
    PIPELINE_INTEGRATION_GOOD = {
        "pipeline_name": "knowledge_qa_pipeline",
        "components": [
            {"name": "document_retriever", "type": "retriever", "config": {"top_k": 5}},
            {
                "name": "answer_generator",
                "type": "generator",
                "config": {"model": "gpt-3.5-turbo"},
            },
        ],
        "connections": [
            {"from": "document_retriever", "to": "answer_generator.documents"}
        ],
        "validation_mode": "strict",
        "error_propagation": "stop_on_error",
    }

    PIPELINE_INTEGRATION_BAD = {
        "pipeline_name": None,  # Missing pipeline name breaks identification
        "components": "invalid_format",  # Should be list, not string
        "connections": [],  # Empty connections break data flow
        "validation_mode": "unknown_mode",  # Invalid validation mode
        "error_propagation": "",  # Empty error handling breaks pipeline
    }


class LangGraphProblems:
    """LangGraph-specific problem scenarios based on 245+ documented GitHub issues."""

    # State management failures (78+ issues)
    STATE_MANAGEMENT_GOOD = {
        "workflow_id": "business_process_001",
        "initial_state": {
            "customer_request": "Process new account application",
            "status": "initiated",
            "assigned_agent": "account_processor",
            "priority": "normal",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "workflow_version": "v2.1",
            },
        },
        "state_validation": True,
        "persistence_config": {"save_interval": 30, "backup_enabled": True},
    }

    STATE_MANAGEMENT_BAD = {
        "workflow_id": "",  # Empty workflow ID breaks state tracking
        "initial_state": None,  # Missing initial state breaks workflow start
        "state_validation": "invalid",  # Should be boolean, not string
        "persistence_config": "not_a_dict",  # Should be dict, not string
    }

    # Agent coordination problems (89+ issues)
    AGENT_COORDINATION_GOOD = {
        "coordination_id": "multi_agent_workflow_001",
        "agents": [
            {"id": "validator", "role": "input_validation", "status": "ready"},
            {"id": "processor", "role": "data_processing", "status": "ready"},
            {"id": "approver", "role": "final_approval", "status": "ready"},
        ],
        "communication_protocol": "sequential",
        "timeout_config": {"agent_response_timeout": 300, "workflow_timeout": 1800},
        "error_recovery": "retry_with_backoff",
    }

    AGENT_COORDINATION_BAD = {
        "coordination_id": None,  # Missing coordination ID breaks tracking
        "agents": [],  # Empty agents list breaks coordination
        "communication_protocol": "unknown_protocol",  # Invalid protocol
        "timeout_config": None,  # Missing timeout config causes hangs
        "error_recovery": "",  # Empty error recovery breaks resilience
    }

    # Graph execution errors (52+ issues)
    GRAPH_EXECUTION_GOOD = {
        "graph_id": "approval_workflow_graph",
        "nodes": [
            {"id": "start", "type": "entry", "config": {"validation": True}},
            {
                "id": "process",
                "type": "action",
                "config": {"handler": "process_request"},
            },
            {
                "id": "approve",
                "type": "decision",
                "config": {"criteria": "business_rules"},
            },
        ],
        "edges": [
            {"from": "start", "to": "process", "condition": "valid_input"},
            {"from": "process", "to": "approve", "condition": "processing_complete"},
        ],
        "execution_mode": "synchronous",
    }

    GRAPH_EXECUTION_BAD = {
        "graph_id": "",  # Empty graph ID breaks execution tracking
        "nodes": "invalid_format",  # Should be list, not string
        "edges": None,  # Missing edges breaks graph connectivity
        "execution_mode": "unknown_mode",  # Invalid execution mode
    }


class SemanticKernelProblems:
    """SemanticKernel-specific problem scenarios based on 178+ documented GitHub issues."""

    # Plugin execution failures (67+ issues)
    PLUGIN_EXECUTION_GOOD = {
        "plugin_id": "business_automation_plugin",
        "function_name": "process_customer_request",
        "parameters": {
            "customer_id": "CUST_12345",
            "request_type": "account_update",
            "priority": "normal",
            "context": {"session_id": "session_789", "user_role": "customer_service"},
        },
        "execution_config": {
            "timeout": 30,
            "retry_count": 3,
            "validation_enabled": True,
        },
        "auth_context": {
            "user_id": "agent_001",
            "permissions": ["customer_data_access", "account_modification"],
        },
    }

    PLUGIN_EXECUTION_BAD = {
        "plugin_id": "",  # Empty plugin ID breaks execution
        "function_name": None,  # Missing function name breaks plugin call
        "parameters": "invalid_format",  # Should be dict, not string
        "execution_config": None,  # Missing config breaks execution control
        "auth_context": "",  # Empty auth context breaks security
    }

    # Semantic function problems (45+ issues)
    SEMANTIC_FUNCTION_GOOD = {
        "function_id": "customer_intent_classifier",
        "prompt_template": "Classify the customer intent: {{$input}}. Return: category, confidence, reasoning",
        "input_variables": {"input": "I need help updating my billing address"},
        "model_config": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 500,
        },
        "validation_rules": {
            "required_fields": ["category", "confidence"],
            "confidence_threshold": 0.7,
        },
    }

    SEMANTIC_FUNCTION_BAD = {
        "function_id": None,  # Missing function ID breaks identification
        "prompt_template": "",  # Empty template breaks function execution
        "input_variables": "not_a_dict",  # Should be dict, not string
        "model_config": None,  # Missing model config breaks execution
        "validation_rules": "",  # Empty validation breaks quality control
    }

    # Memory and context issues (39+ issues)
    MEMORY_CONTEXT_GOOD = {
        "memory_id": "customer_conversation_memory",
        "context_data": {
            "conversation_history": [
                {"role": "customer", "content": "I need help with my account"},
                {"role": "agent", "content": "I can help you with that"},
            ],
            "customer_profile": {
                "id": "CUST_12345",
                "tier": "premium",
                "preferences": ["email_notifications"],
            },
        },
        "memory_config": {
            "max_history_length": 10,
            "compression_enabled": True,
            "persistence_enabled": True,
        },
        "retrieval_settings": {"similarity_threshold": 0.8, "max_results": 5},
    }

    MEMORY_CONTEXT_BAD = {
        "memory_id": "",  # Empty memory ID breaks context tracking
        "context_data": None,  # Missing context data breaks memory
        "memory_config": "invalid_format",  # Should be dict, not string
        "retrieval_settings": "",  # Empty retrieval settings breaks memory access
    }


def get_framework_problems(framework: str) -> Dict[str, Any]:
    """Get problem scenarios for a specific framework."""
    problems = {
        "autogen": {
            "conversation_flow": {
                "good": AutoGenProblems.CONVERSATION_FLOW_GOOD,
                "bad": AutoGenProblems.CONVERSATION_FLOW_BAD,
                "github_issue": "#6819",
                "business_impact": "Research collaboration workflows break on malformed conversation data",
            },
            "function_calls": {
                "good": AutoGenProblems.FUNCTION_CALL_GOOD,
                "bad": AutoGenProblems.FUNCTION_CALL_BAD,
                "github_issue": "#5736",
                "business_impact": "Tool integration fails when function arguments are malformed",
            },
            "message_handling": {
                "good": AutoGenProblems.MESSAGE_HANDLING_GOOD,
                "bad": AutoGenProblems.MESSAGE_HANDLING_BAD,
                "github_issue": "#6123",
                "business_impact": "Agent-to-agent message passing corrupts due to validation failures",
            },
        },
        "langchain": {
            "structured_output": {
                "good": LangChainProblems.CHAIN_INPUT_GOOD,
                "bad": LangChainProblems.CHAIN_INPUT_BAD,
                "github_issue": "#32687",
                "business_impact": "Customer service chains break when LLMs return unexpected structured output formats",
            },
            "message_format": {
                "good": LangChainProblems.MEMORY_CONTEXT_GOOD,
                "bad": LangChainProblems.MEMORY_CONTEXT_BAD,
                "github_issue": "#31800",
                "business_impact": "Chatbot conversations fail when message format validation errors occur",
            },
            "tool_validation": {
                "good": {
                    "tool_name": "customer_lookup",
                    "tool_input": {
                        "customer_id": "CUST_12345",
                        "search_type": "account_details",
                        "include_history": True,
                    },
                    "caller": "customer_service_agent",
                    "expected_output": "customer_data",
                },
                "bad": {
                    "tool_name": None,  # Missing tool name breaks validation
                    "tool_input": "invalid_format",  # Should be dict, not string
                    "caller": "",  # Empty caller breaks tool routing
                    "expected_output": None,  # Missing output type breaks chain
                },
                "github_issue": "#31536",
                "business_impact": "Tool calls fail with validation errors causing chain breakdowns",
            },
        },
        "crewai": {
            "crew_coordination": {
                "good": CrewAIProblems.CREW_COORDINATION_GOOD,
                "bad": CrewAIProblems.CREW_COORDINATION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Multi-agent crews fail to coordinate when task data is malformed",
            },
            "agent_roles": {
                "good": CrewAIProblems.AGENT_ROLES_GOOD,
                "bad": CrewAIProblems.AGENT_ROLES_BAD,
                "github_issue": "Multiple",
                "business_impact": "Agent role mismatches break task assignment and collaboration",
            },
        },
        "llamaindex": {
            "document_ingestion": {
                "good": LlamaIndexProblems.DOCUMENT_INGESTION_GOOD,
                "bad": LlamaIndexProblems.DOCUMENT_INGESTION_BAD,
                "github_issue": "#19696",
                "business_impact": "Document processing fails causing knowledge base corruption and data loss",
            },
            "vector_query": {
                "good": LlamaIndexProblems.VECTOR_QUERY_GOOD,
                "bad": LlamaIndexProblems.VECTOR_QUERY_BAD,
                "github_issue": "#19508",
                "business_impact": "Vector store queries return empty results breaking knowledge retrieval",
            },
            "node_serialization": {
                "good": LlamaIndexProblems.NODE_SERIALIZATION_GOOD,
                "bad": LlamaIndexProblems.NODE_SERIALIZATION_BAD,
                "github_issue": "#19387",
                "business_impact": "Knowledge base persistence fails causing data corruption and loss",
            },
        },
        "haystack": {
            "document_processing": {
                "good": HaystackProblems.DOCUMENT_PROCESSING_GOOD,
                "bad": HaystackProblems.DOCUMENT_PROCESSING_BAD,
                "github_issue": "Multiple",
                "business_impact": "Document processing pipelines crash with malformed content breaking knowledge systems",
            },
            "search_retrieval": {
                "good": HaystackProblems.SEARCH_RETRIEVAL_GOOD,
                "bad": HaystackProblems.SEARCH_RETRIEVAL_BAD,
                "github_issue": "Multiple",
                "business_impact": "Search retrieval fails with poor quality data breaking knowledge access",
            },
            "pipeline_integration": {
                "good": HaystackProblems.PIPELINE_INTEGRATION_GOOD,
                "bad": HaystackProblems.PIPELINE_INTEGRATION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Pipeline component integration fails breaking end-to-end knowledge workflows",
            },
        },
        "langgraph": {
            "state_management": {
                "good": LangGraphProblems.STATE_MANAGEMENT_GOOD,
                "bad": LangGraphProblems.STATE_MANAGEMENT_BAD,
                "github_issue": "Multiple",
                "business_impact": "Workflow state corruption breaks business process automation",
            },
            "agent_coordination": {
                "good": LangGraphProblems.AGENT_COORDINATION_GOOD,
                "bad": LangGraphProblems.AGENT_COORDINATION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Multi-agent coordination fails breaking collaborative workflows",
            },
            "graph_execution": {
                "good": LangGraphProblems.GRAPH_EXECUTION_GOOD,
                "bad": LangGraphProblems.GRAPH_EXECUTION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Graph execution errors break workflow orchestration and automation",
            },
        },
        "semantickernel": {
            "plugin_execution": {
                "good": SemanticKernelProblems.PLUGIN_EXECUTION_GOOD,
                "bad": SemanticKernelProblems.PLUGIN_EXECUTION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Plugin execution failures break AI orchestration and automation",
            },
            "semantic_function": {
                "good": SemanticKernelProblems.SEMANTIC_FUNCTION_GOOD,
                "bad": SemanticKernelProblems.SEMANTIC_FUNCTION_BAD,
                "github_issue": "Multiple",
                "business_impact": "Semantic function errors break AI reasoning and processing workflows",
            },
            "memory_context": {
                "good": SemanticKernelProblems.MEMORY_CONTEXT_GOOD,
                "bad": SemanticKernelProblems.MEMORY_CONTEXT_BAD,
                "github_issue": "Multiple",
                "business_impact": "Memory context corruption breaks conversation continuity and context awareness",
            },
        },
    }

    return problems.get(framework, {})


def get_problem_summary(framework: str) -> str:
    """Get a summary of documented problems for a framework."""
    summaries = {
        "autogen": """AutoGen Framework - 54+ Documented Validation Issues:
• Multi-agent conversation flow breakdowns (#6819)
• Function/tool call argument validation failures (#5736)
• Internal message handling corruption (#6123)
• Structured output parsing errors (#6727, #6638)
• Model integration inconsistencies (#5075, #5020)

Business Impact: Research collaboration workflows fail, agent coordination breaks, tool integration becomes unreliable.""",
        "langchain": """LangChain Framework - 525+ Documented Validation Issues:
• Chain input validation failures cause processing breaks
• Memory and context management errors lose conversation state
• Tool integration failures from malformed data
• Model switching issues from inconsistent formats
• Prompt template validation errors break chains

Business Impact: Customer service chains fail, conversation context is lost, automated workflows become unreliable.""",
        "crewai": """CrewAI Framework - Multiple Documented Coordination Issues:
• Crew coordination failures from malformed task data
• Agent role and capability mismatches break assignments
• Task distribution errors cause workflow failures
• Inter-agent communication validation problems
• Mission objective parsing errors confuse crews

Business Impact: Multi-agent teams fail to coordinate, business process automation breaks, collaborative workflows become unreliable.""",
        "llamaindex": """LlamaIndex Framework - 949+ Documented Validation Issues:
• Document ingestion failures cause knowledge base corruption (#19696)
• Vector store queries return empty responses breaking retrieval (#19508)
• Node serialization failures corrupt knowledge persistence (#19387)
• Pipeline data quality issues break large-scale processing (#19712)
• Query validation problems cause search system failures (#19643)

Business Impact: Knowledge management systems fail, enterprise documentation becomes unreliable, RAG applications break in production.""",
        "haystack": """Haystack Framework - 347+ Documented Validation Issues:
• Document processing pipeline failures crash with malformed content (89+ issues)
• Retrieval quality problems with poor scoring and empty queries (134+ issues)
• Component integration breakdowns across pipeline stages (67+ issues)
• Search result inconsistencies and missing confidence scores (57+ issues)

Business Impact: Knowledge management systems break, search quality degrades, pipeline reliability becomes unreliable.""",
        "langgraph": """LangGraph Framework - 245+ Documented Validation Issues:
• State management failures corrupt workflow execution (78+ issues)
• Agent coordination problems break multi-agent scenarios (89+ issues)
• Graph execution errors cause workflow failures (52+ issues)
• Data flow validation problems break pipeline stages (26+ issues)

Business Impact: Workflow automation breaks, business process orchestration fails, collaborative AI systems become unreliable.""",
        "semantickernel": """SemanticKernel Framework - 178+ Documented Validation Issues:
• Plugin execution failures break AI orchestration (67+ issues)
• Semantic function problems corrupt AI reasoning (45+ issues)
• Memory and context issues lose conversation state (39+ issues)
• Planning and orchestration errors break workflows (27+ issues)

Business Impact: AI orchestration breaks, plugin systems fail, enterprise integration becomes unreliable.""",
    }

    return summaries.get(framework, f"No documented problems found for {framework}")


if __name__ == "__main__":
    # Demo the problem scenarios
    print("🚨 ADRI Problem Demonstration - GitHub Issue Scenarios")
    print("=" * 60)

    for framework in [
        "autogen",
        "langchain",
        "crewai",
        "llamaindex",
        "haystack",
        "langgraph",
        "semantickernel",
    ]:
        print(f"\n📋 {framework.upper()} FRAMEWORK PROBLEMS:")
        print(get_problem_summary(framework))
        print()

        problems = get_framework_problems(framework)
        for problem_name, problem_data in problems.items():
            print(f"   🔧 {problem_name}: GitHub {problem_data['github_issue']}")
            print(f"      💼 Impact: {problem_data['business_impact']}")
