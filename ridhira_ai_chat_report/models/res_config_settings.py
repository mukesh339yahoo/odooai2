# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ridhira_llm_provider = fields.Selection([
        ('gemini', 'Google Gemini (Fast & Generous Free Tier)'),
        ('openai', 'OpenAI (GPT-4o / GPT-4o Mini)'),
        ('anthropic', 'Anthropic (Claude 3.5 Sonnet)'),
        ('groq', 'Groq (Ultra-Fast Blazing Inference)'),
        ('ollama', 'Ollama (Local / On-Premise 100% Private)'),
        ('custom', 'Custom OpenAI-Compatible (DeepSeek, OpenRouter, Azure)'),
    ], string="LLM Provider", default='gemini', config_parameter='ridhira_ai_chat_report.llm_provider')
    
    # OpenAI Settings
    ridhira_openai_api_key = fields.Char(string="OpenAI API Key", config_parameter='ridhira_ai_chat_report.openai_api_key')
    ridhira_openai_model = fields.Selection([
        ('gpt-4o', 'GPT-4o (Recommended)'),
        ('gpt-4o-mini', 'GPT-4o Mini (Fast & Economical)'),
        ('o1-mini', 'o1 Mini (Advanced Reasoning)'),
    ], string="OpenAI Model", default='gpt-4o', config_parameter='ridhira_ai_chat_report.openai_model')

    # Gemini Settings
    ridhira_gemini_api_key = fields.Char(string="Gemini API Key", config_parameter='ridhira_ai_chat_report.gemini_api_key')
    ridhira_gemini_model = fields.Selection([
        ('gemini-2.0-flash', 'Gemini 2.0 Flash (Fastest, Recommended)'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro (Deep Multimodal & Reasoning)'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
    ], string="Gemini Model", default='gemini-2.0-flash', config_parameter='ridhira_ai_chat_report.gemini_model')

    # Anthropic Settings
    ridhira_anthropic_api_key = fields.Char(string="Anthropic API Key", config_parameter='ridhira_ai_chat_report.anthropic_api_key')
    ridhira_anthropic_model = fields.Selection([
        ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet (Recommended)'),
        ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku (Fast)'),
    ], string="Anthropic Model", default='claude-3-5-sonnet-20241022', config_parameter='ridhira_ai_chat_report.anthropic_model')

    # Groq Settings (Blazing speed)
    ridhira_groq_api_key = fields.Char(string="Groq API Key", config_parameter='ridhira_ai_chat_report.groq_api_key')
    ridhira_groq_model = fields.Selection([
        ('llama-3.3-70b-versatile', 'Llama 3.3 70B (Versatile, Recommended)'),
        ('llama-3.1-8b-instant', 'Llama 3.1 8B (Instant Speed)'),
        ('mixtral-8x7b-32768', 'Mixtral 8x7B (Large Context)'),
    ], string="Groq Model", default='llama-3.3-70b-versatile', config_parameter='ridhira_ai_chat_report.groq_model')

    # Ollama Local Settings (On-Premise Privacy)
    ridhira_ollama_endpoint = fields.Char(
        string="Ollama Endpoint", 
        default="http://localhost:11434", 
        config_parameter='ridhira_ai_chat_report.ollama_endpoint',
        help="Local or remote Ollama server URL e.g. http://localhost:11434"
    )
    ridhira_ollama_model = fields.Char(
        string="Ollama Model", 
        default="llama3.2", 
        config_parameter='ridhira_ai_chat_report.ollama_model',
        help="e.g. llama3.2, mistral, qwen2.5, deepseek-r1"
    )

    # Custom OpenAI-Compatible (DeepSeek, OpenRouter, LocalAI)
    ridhira_custom_endpoint = fields.Char(
        string="API Base URL", 
        default="https://api.deepseek.com/v1", 
        config_parameter='ridhira_ai_chat_report.custom_endpoint',
        help="Base URL of OpenAI-compatible API endpoint"
    )
    ridhira_custom_api_key = fields.Char(string="Custom API Key", config_parameter='ridhira_ai_chat_report.custom_api_key')
    ridhira_custom_model = fields.Char(
        string="Custom Model", 
        default="deepseek-chat", 
        config_parameter='ridhira_ai_chat_report.custom_model'
    )

    # Feature Toggles
    ridhira_enable_ai_insights = fields.Boolean(
        string="Generate Executive AI Insights",
        default=True,
        config_parameter='ridhira_ai_chat_report.enable_ai_insights',
        help="Automatically generate business takeaways and recommendations alongside the visual report."
    )
    ridhira_enable_voice_input = fields.Boolean(
        string="Enable Voice Query Bar",
        default=True,
        config_parameter='ridhira_ai_chat_report.enable_voice_input',
        help="Allow users to speak queries using microphone speech-to-text directly in the query bar."
    )
