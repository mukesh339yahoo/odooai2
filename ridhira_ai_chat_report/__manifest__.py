# -*- coding: utf-8 -*-
{
    'name': 'AI Chat-to-Report & Dashboard Assistant',
    'version': '20.0.1.0.0',
    'category': 'Productivity/Dashboard',
    'summary': 'The Ultimate AI Data Analyst for Odoo 20: Voice-to-Report, Multi-LLM (Gemini, OpenAI, Claude, Groq, Ollama), Executive Insights & Conversational Refinement.',
    'description': """
        AI Chat-to-Report & Dashboard Assistant (Odoo 20 Enterprise / Community)
        ========================================================================
        Turn natural speech and plain English into instant visual reports, charts, and pivot tables.
        
        Key Marketplace Highlights:
        ---------------------------
        - Voice-to-Report: Speak prompts with browser speech recognition.
        - Multi-LLM Support: Google Gemini 2.0, OpenAI GPT-4o, Anthropic Claude 3.5, Groq, Local Ollama & DeepSeek.
        - Executive AI Insights: Automatic strategic takeaways and business observations alongside reports.
        - Conversational Refinement: Modify reports conversationally with follow-up instructions.
        - Native Odoo 20: Built entirely with OWL 3 and native ORM architecture.
        - 100% Data Privacy: Translates queries locally; enterprise business data never leaves your server.
    """,
    'author': 'Ridhira Technologies , Pune , India',
    'website': 'https://ridhira.desigoogly.com',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'web', 'board'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/ai_report_query_views.xml',
        'views/ai_report_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ridhira_ai_chat_report/static/src/css/ai_report.scss',
            'ridhira_ai_chat_report/static/src/components/ai_query_bar/ai_query_bar.xml',
            'ridhira_ai_chat_report/static/src/components/ai_query_bar/ai_query_bar.js',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}

