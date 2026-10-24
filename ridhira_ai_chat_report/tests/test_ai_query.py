# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch
import json


class TestAiQuery(TransactionCase):

    def setUp(self):
        super().setUp()
        self.AiReportQuery = self.env['ai.report.query']

    def test_basic_instantiation(self):
        """
        Verify basic model structure and default values.
        """
        query_record = self.AiReportQuery.create({
            'name': 'Test Query',
            'user_prompt': 'Show me sales from last 30 days',
        })
        self.assertEqual(query_record.name, 'Test Query')
        self.assertEqual(query_record.chart_type, 'bar')
        
    def test_missing_api_key(self):
        """
        Test that action_generate_query fails gracefully when no API keys are configured.
        """
        query_record = self.AiReportQuery.create({
            'name': 'Test Missing Key',
            'user_prompt': 'Hello',
        })
        with self.assertRaises(UserError):
            query_record.action_generate_query(query_record.user_prompt)

    @patch('odoo.addons.ridhira_ai_chat_report.models.ai_report_query.AiReportQuery._get_llm_response')
    def test_usecase_grouped_pie_chart(self, mock_get_llm_response):
        """
        Use Case: "Show me partners grouped by country as a pie chart"
        (Using res.partner to guarantee it runs on base Odoo without optional apps installed)
        """
        mock_get_llm_response.side_effect = [
            json.dumps({"model_name": "res.partner"}),  # Step 1 response
            json.dumps({
                "domain": [],
                "fields_list": ["name", "country_id"],
                "groupby": ["country_id"],
                "chart_type": "pie"
            })  # Step 2 response
        ]
        
        query_record = self.AiReportQuery.create({
            'name': 'Partners by Country',
            'user_prompt': 'Show me partners grouped by country as a pie chart',
        })
        
        result = query_record.action_generate_query(query_record.user_prompt)
        
        self.assertEqual(result['model_name'], 'res.partner')
        self.assertEqual(result['chart_type'], 'pie')
        self.assertIn('country_id', result['groupby'])
        self.assertIn('action', result)
        self.assertEqual(result['action']['view_mode'], 'graph,list')
        self.assertEqual(result['action']['context']['graph_mode'], 'pie')
        
    @patch('odoo.addons.ridhira_ai_chat_report.models.ai_report_query.AiReportQuery._get_llm_response')
    def test_usecase_pivot_table(self, mock_get_llm_response):
        """
        Use Case: "Show me active users grouped by company in a pivot table"
        """
        mock_get_llm_response.side_effect = [
            json.dumps({"model_name": "res.users"}), 
            json.dumps({
                "domain": [["active", "=", True]],
                "fields_list": ["name", "company_id"],
                "groupby": ["company_id"],
                "chart_type": "pivot"
            })
        ]
        
        query_record = self.AiReportQuery.create({
            'name': 'Users Pivot',
            'user_prompt': 'Show me active users grouped by company in a pivot table',
        })
        
        result = query_record.action_generate_query(query_record.user_prompt)
        
        self.assertEqual(result['model_name'], 'res.users')
        self.assertEqual(result['chart_type'], 'pivot')
        self.assertIn('company_id', result['groupby'])
        self.assertEqual(result['domain'], [["active", "=", True]])
        self.assertEqual(result['action']['view_mode'], 'pivot,list')

    @patch('odoo.addons.ridhira_ai_chat_report.models.ai_report_query.AiReportQuery._get_llm_response')
    def test_markdown_json_response_handling(self, mock_get_llm_response):
        """
        Verify that LLM responses wrapped in markdown ```json ... ``` blocks are parsed properly.
        """
        mock_get_llm_response.side_effect = [
            "```json\n{\"model_name\": \"res.partner\"}\n```",
            "```json\n{\n  \"domain\": [],\n  \"fields_list\": [\"name\"],\n  \"groupby\": [],\n  \"chart_type\": \"bar\"\n}\n```"
        ]
        
        query_record = self.AiReportQuery.create({
            'name': 'Markdown JSON Test',
            'user_prompt': 'Show me all partners',
        })
        
        result = query_record.action_generate_query(query_record.user_prompt)
        self.assertEqual(result['model_name'], 'res.partner')
        self.assertEqual(result['chart_type'], 'bar')

    @patch('odoo.addons.ridhira_ai_chat_report.models.ai_report_query.AiReportQuery._get_llm_response')
    def test_usecase_invalid_model(self, mock_get_llm_response):
        """
        Use Case: User types gibberish or LLM hallucinates a non-existent model
        """
        mock_get_llm_response.side_effect = [
            json.dumps({"model_name": "fake.model.that.does.not.exist"}), 
        ]
        
        query_record = self.AiReportQuery.create({
            'name': 'Invalid Model Query',
            'user_prompt': 'asdasdasd',
        })
        
        with self.assertRaisesRegex(UserError, "Could not identify a valid Odoo model"):
            query_record.action_generate_query(query_record.user_prompt)

    def test_action_open_report(self):
        """
        Test re-running / opening a saved report action.
        """
        record = self.AiReportQuery.create({
            'name': 'Saved Partner Query',
            'user_prompt': 'List partners',
            'model_name': 'res.partner',
            'domain': json.dumps([]),
            'groupby': json.dumps(['country_id']),
            'chart_type': 'bar',
        })
        action = record.action_open_report()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['view_mode'], 'graph,list')
        self.assertEqual(action['context']['graph_mode'], 'bar')
