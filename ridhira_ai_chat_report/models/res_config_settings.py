# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ridhira_llm_provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('gemini', 'Google Gemini'),
        ('anthropic', 'Anthropic')
    ], string="LLM Provider", default='gemini', config_parameter='ridhira_ai_chat_report.llm_provider')
    
    ridhira_openai_api_key = fields.Char(string="OpenAI API Key", config_parameter='ridhira_ai_chat_report.openai_api_key')
    ridhira_openai_model = fields.Selection([
        ('gpt-4o', 'GPT-4o (Recommended)'),
        ('gpt-4o-mini', 'GPT-4o Mini (Fast & Economical)'),
        ('o1-mini', 'o1 Mini (Advanced Reasoning)'),
    ], string="OpenAI Model", default='gpt-4o', config_parameter='ridhira_ai_chat_report.openai_model')

    ridhira_gemini_api_key = fields.Char(string="Gemini API Key", config_parameter='ridhira_ai_chat_report.gemini_api_key')
    ridhira_gemini_model = fields.Selection([
        ('gemini-2.0-flash', 'Gemini 2.0 Flash (Fastest, Recommended)'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro (Deep Multimodal & Reasoning)'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
    ], string="Gemini Model", default='gemini-2.0-flash', config_parameter='ridhira_ai_chat_report.gemini_model')

    ridhira_anthropic_api_key = fields.Char(string="Anthropic API Key", config_parameter='ridhira_ai_chat_report.anthropic_api_key')
    ridhira_anthropic_model = fields.Selection([
        ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet (Recommended)'),
        ('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku (Fast)'),
    ], string="Anthropic Model", default='claude-3-5-sonnet-20241022', config_parameter='ridhira_ai_chat_report.anthropic_model')

