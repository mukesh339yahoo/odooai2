# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
import json
import re
import requests


def _clean_json_response(raw_text):
    """
    Safely extract JSON from raw LLM responses that may be wrapped
    in markdown fences (```json ... ```) or have surrounding conversational text.
    """
    if not raw_text:
        return ""
    text = raw_text.strip()
    # Strip markdown code blocks if present
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    
    # In case there is still non-JSON text surrounding the braces
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


class AiReportQuery(models.Model):
    _name = 'ai.report.query'
    _description = 'AI Report Query'
    _order = 'id desc'

    name = fields.Char(string='Query Name', required=True)
    user_prompt = fields.Text(string='User Prompt', required=True)
    model_name = fields.Char(string='Target Model')
    domain = fields.Text(string='Domain (JSON)')
    fields_list = fields.Text(string='Fields (JSON)')
    groupby = fields.Text(string='Group By (JSON)')
    measure = fields.Char(string='Measure Field')
    chart_type = fields.Selection([
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Chart'),
        ('pivot', 'Pivot Table'),
    ], string='Chart Type', default='bar')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Created On', readonly=True)

    def _get_llm_response(self, prompt):
        """
        Query the configured LLM Provider (OpenAI, Gemini, Anthropic) with timeout protection
        and dynamic model configuration for Odoo 20.
        """
        provider = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.llm_provider', 'gemini')
        timeout = 40  # Seconds
        
        if provider == 'openai':
            api_key = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.openai_api_key')
            if not api_key:
                raise UserError(_("OpenAI API Key is not configured in Settings."))
            
            model = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.openai_model', 'gpt-4o')
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            try:
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=timeout)
            except requests.exceptions.RequestException as e:
                raise UserError(_("OpenAI Connection Error: %s") % str(e))
                
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                raise UserError(_("OpenAI API Error (%s): %s") % (response.status_code, response.text))
                
        elif provider == 'gemini':
            api_key = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.gemini_api_key')
            if not api_key:
                raise UserError(_("Gemini API Key is not configured in Settings."))
            
            model = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.gemini_model', 'gemini-2.0-flash')
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            except requests.exceptions.RequestException as e:
                raise UserError(_("Gemini Connection Error: %s") % str(e))
                
            if response.status_code == 200:
                data = response.json()
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    raise UserError(_("Invalid response structure received from Gemini."))
            else:
                raise UserError(_("Gemini API Error (%s): %s") % (response.status_code, response.text))
                
        elif provider == 'anthropic':
            api_key = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.anthropic_api_key')
            if not api_key:
                raise UserError(_("Anthropic API Key is not configured in Settings."))
            
            model = self.env['ir.config_parameter'].sudo().get_param('ridhira_ai_chat_report.anthropic_model', 'claude-3-5-sonnet-20241022')
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            full_prompt = prompt + "\nRespond with ONLY valid JSON."
            payload = {
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": full_prompt}]
            }
            try:
                response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=timeout)
            except requests.exceptions.RequestException as e:
                raise UserError(_("Anthropic Connection Error: %s") % str(e))
                
            if response.status_code == 200:
                data = response.json()
                try:
                    return data['content'][0]['text']
                except (KeyError, IndexError):
                    raise UserError(_("Invalid response structure received from Anthropic."))
            else:
                raise UserError(_("Anthropic API Error (%s): %s") % (response.status_code, response.text))

        raise UserError(_("Invalid LLM Provider configured: %s") % provider)

    @api.model
    def action_generate_query(self, user_prompt):
        """
        Translates user natural language prompt into Odoo ORM parameters.
        Returns a dict with domain, fields, groupby, model_name, chart_type, measure, and action.
        """
        if not user_prompt or not user_prompt.strip():
            raise UserError(_("Please provide a query prompt."))

        # Step 1: Identify Target Model
        step1_prompt = f"""
        You are an Odoo ORM expert. The user wants to generate a report based on this query: "{user_prompt}"
        Identify the primary Odoo model they are referring to (e.g., 'sale.order', 'purchase.order', 'account.move', 'crm.lead', 'res.partner', 'stock.picking', 'project.task', 'hr.expense').
        Return ONLY a JSON object with the key "model_name". For example: {{"model_name": "sale.order"}}
        """
        
        step1_res = self._get_llm_response(step1_prompt)
        cleaned_step1 = _clean_json_response(step1_res)
        try:
            model_name = json.loads(cleaned_step1).get('model_name')
        except Exception:
            raise UserError(_("Failed to parse LLM response for model identification."))
            
        if not model_name or model_name not in self.env:
            raise UserError(_("Could not identify a valid Odoo model from your query: %s") % (model_name or 'None'))

        # Security check: Ensure current user has read rights to the target model
        try:
            self.env[model_name].check_access_rights('read')
        except (AccessError, Exception):
            raise UserError(_("You do not have permission to access data from the '%s' model.") % model_name)
            
        # Step 2: Fetch field metadata for the model
        fields_info = self.env['ir.model.fields'].sudo().search_read(
            [('model', '=', model_name), ('ttype', 'in', ['char', 'integer', 'float', 'monetary', 'many2one', 'selection', 'date', 'datetime'])],
            ['name', 'field_description', 'ttype']
        )
        
        fields_context = [{"name": f['name'], "desc": f['field_description'], "type": f['ttype']} for f in fields_info]
        fields_context_str = json.dumps(fields_context[:120])
        
        step2_prompt = f"""
        You are an Odoo ORM expert. The user wants a report based on this query: "{user_prompt}"
        The target model is '{model_name}'.
        Here are available fields: {fields_context_str}
        
        Generate a JSON object with the following keys:
        - "domain": A valid Odoo domain list (e.g., [("state", "=", "sale")]). If no filter is needed, use [].
        - "fields_list": A list of field names to read. Must include any field used in groupby and any numeric field to measure.
        - "groupby": A list of field names to group by. (e.g., ["partner_id"] or ["date:month"]). If none, use [].
        - "measure": A numeric field name (type 'float', 'monetary', or 'integer') to aggregate/measure (e.g., "amount_total" or "__count__"). If count only, use "__count__".
        - "chart_type": One of "bar", "pie", "line", "pivot".
        
        Return ONLY the JSON object.
        """
        
        step2_res = self._get_llm_response(step2_prompt)
        cleaned_step2 = _clean_json_response(step2_res)
        try:
            query_data = json.loads(cleaned_step2)
        except Exception:
            raise UserError(_("Failed to parse LLM response for query generation."))
            
        model_fields = self.env[model_name].fields_get()
        raw_fields = query_data.get('fields_list', [])
        valid_fields = [f for f in raw_fields if f in model_fields]

        raw_groupby = query_data.get('groupby', [])
        # Handle field or field:interval like create_date:month
        valid_groupby = []
        for g in raw_groupby:
            base_field = g.split(':')[0] if isinstance(g, str) else g
            if base_field in model_fields:
                valid_groupby.append(g)

        raw_measure = query_data.get('measure')
        valid_measure = raw_measure if (raw_measure in model_fields or raw_measure == '__count__') else False
        
        if not valid_fields:
            valid_fields = ['display_name']

        chart_type = query_data.get('chart_type', 'bar')
        if chart_type not in ['bar', 'pie', 'line', 'pivot']:
            chart_type = 'bar'

        domain = query_data.get('domain', [])
        if not isinstance(domain, list):
            domain = []

        # Build action dictionary for Odoo 20
        is_pivot = (chart_type == 'pivot')
        views = [[False, 'pivot' if is_pivot else 'graph'], [False, 'list']]
        context = {
            'group_by': valid_groupby,
            'graph_mode': chart_type if not is_pivot else 'bar',
        }
        if valid_measure and valid_measure != '__count__':
            context['graph_measure'] = valid_measure
            context['pivot_measures'] = [valid_measure]

        if valid_groupby:
            context['graph_groupbys'] = valid_groupby
            context['pivot_row_groupby'] = valid_groupby

        action_def = {
            'type': 'ir.actions.act_window',
            'name': f"AI: {user_prompt[:40]}",
            'res_model': model_name,
            'view_mode': f"{'pivot' if is_pivot else 'graph'},list",
            'views': views,
            'domain': domain,
            'context': context,
            'target': 'current',
        }

        # Persist query record for user history
        query_record = False
        try:
            query_record = self.create({
                'name': user_prompt[:80],
                'user_prompt': user_prompt,
                'model_name': model_name,
                'domain': json.dumps(domain),
                'fields_list': json.dumps(valid_fields),
                'groupby': json.dumps(valid_groupby),
                'measure': valid_measure or '',
                'chart_type': chart_type,
                'user_id': self.env.user.id,
            })
        except Exception:
            pass

        return {
            'query_id': query_record.id if query_record else False,
            'model_name': model_name,
            'domain': domain,
            'fields_list': valid_fields,
            'groupby': valid_groupby,
            'measure': valid_measure or '',
            'chart_type': chart_type,
            'action': action_def,
        }

    def action_open_report(self):
        """
        Re-run or view the report for a saved query record.
        """
        self.ensure_one()
        domain = []
        if self.domain:
            try:
                domain = json.loads(self.domain)
            except Exception:
                domain = []

        groupby = []
        if self.groupby:
            try:
                groupby = json.loads(self.groupby)
            except Exception:
                groupby = []

        is_pivot = (self.chart_type == 'pivot')
        context = {
            'group_by': groupby,
            'graph_mode': self.chart_type if not is_pivot else 'bar',
        }
        if self.measure and self.measure != '__count__':
            context['graph_measure'] = self.measure
            context['pivot_measures'] = [self.measure]

        if groupby:
            context['graph_groupbys'] = groupby
            context['pivot_row_groupby'] = groupby

        return {
            'type': 'ir.actions.act_window',
            'name': f"AI Report: {self.name}",
            'res_model': self.model_name,
            'view_mode': f"{'pivot' if is_pivot else 'graph'},list",
            'views': [[False, 'pivot' if is_pivot else 'graph'], [False, 'list']],
            'domain': domain,
            'context': context,
            'target': 'current',
        }
