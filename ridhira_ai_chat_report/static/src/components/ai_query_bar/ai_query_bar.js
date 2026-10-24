/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";

export class AiQueryBar extends Component {
    static template = "ridhira_ai_chat_report.AiQueryBar";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            isOpen: false,
            prompt: "",
            isLoading: false,
            error: null,
        });

        this.suggestions = [
            "Top 5 customers by sales (bar chart)",
            "Invoices by status as a pie chart",
            "Active leads grouped by stage",
            "Monthly sales trend this year (line chart)",
            "Active users grouped by company (pivot table)",
        ];
    }

    togglePanel() {
        this.state.isOpen = !this.state.isOpen;
        this.state.error = null;
    }

    closePanel() {
        this.state.isOpen = false;
        this.state.error = null;
    }

    setPrompt(suggestion) {
        this.state.prompt = suggestion;
    }

    async submitQuery() {
        const query = this.state.prompt.trim();
        if (!query) return;

        this.state.isLoading = true;
        this.state.error = null;

        try {
            const response = await this.orm.call(
                "ai.report.query",
                "action_generate_query",
                [query]
            );

            this.closePanel();

            if (response.action) {
                await this.action.doAction(response.action);
            } else {
                // Fallback action construction for Odoo 20
                const isPivot = response.chart_type === 'pivot';
                await this.action.doAction({
                    type: "ir.actions.act_window",
                    name: `AI: ${query.slice(0, 40)}`,
                    res_model: response.model_name,
                    view_mode: `${isPivot ? 'pivot' : 'graph'},list`,
                    views: [
                        [false, isPivot ? 'pivot' : 'graph'],
                        [false, "list"]
                    ],
                    domain: response.domain || [],
                    context: {
                        group_by: response.groupby || [],
                        graph_mode: isPivot ? 'bar' : (response.chart_type || 'bar'),
                        ...(response.measure ? { graph_measure: response.measure, pivot_measures: [response.measure] } : {}),
                        ...(response.groupby ? { graph_groupbys: response.groupby, pivot_row_groupby: response.groupby } : {}),
                    },
                    target: "current",
                });
            }
        } catch (error) {
            this.state.error = error.message || (error.data && error.data.message) || "Failed to generate AI report.";
            console.error("AI Report Error:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.submitQuery();
        } else if (ev.key === "Escape") {
            this.closePanel();
        }
    }
}

export class AiReportDashboard extends Component {
    static template = "ridhira_ai_chat_report.AiReportDashboard";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: [Number, String], optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            prompt: "",
            isLoading: false,
            error: null,
            recentQueries: [],
        });

        this.categories = [
            {
                title: "Sales & Revenue",
                icon: "fa-line-chart",
                queries: [
                    "Show sales by customer as a bar chart",
                    "Monthly sales comparison for this year",
                    "Top 10 selling products this quarter",
                ]
            },
            {
                title: "Invoicing & Accounting",
                icon: "fa-file-text-o",
                queries: [
                    "Open customer invoices grouped by payment state",
                    "Total expenses by category as a pie chart",
                    "Monthly revenue breakdown in pivot table",
                ]
            },
            {
                title: "CRM & Pipelines",
                icon: "fa-users",
                queries: [
                    "Opportunity pipeline grouped by stage",
                    "Expected revenue by salesperson",
                    "Leads created in last 30 days by source",
                ]
            },
            {
                title: "Operations & Inventory",
                icon: "fa-cubes",
                queries: [
                    "Stock transfers grouped by operation type",
                    "Purchase orders by vendor as a bar chart",
                    "Deliveries pending this week",
                ]
            }
        ];

        onMounted(() => {
            this.loadRecentQueries();
        });
    }

    async loadRecentQueries() {
        try {
            const records = await this.orm.searchRead(
                "ai.report.query",
                [],
                ["name", "user_prompt", "model_name", "chart_type", "create_date"],
                { limit: 5, order: "id desc" }
            );
            this.state.recentQueries = records;
        } catch (e) {
            this.state.recentQueries = [];
        }
    }

    setPrompt(query) {
        this.state.prompt = query;
    }

    async submitQuery() {
        const query = this.state.prompt.trim();
        if (!query) return;

        this.state.isLoading = true;
        this.state.error = null;

        try {
            const response = await this.orm.call(
                "ai.report.query",
                "action_generate_query",
                [query]
            );

            if (response.action) {
                await this.action.doAction(response.action);
            }
        } catch (error) {
            this.state.error = error.message || (error.data && error.data.message) || "Failed to generate report.";
            console.error(error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async runRecentQuery(record) {
        this.state.prompt = record.user_prompt;
        await this.submitQuery();
    }

    openHistory() {
        this.action.doAction("ridhira_ai_chat_report.action_ai_report_query_history");
    }

    openSettings() {
        this.action.doAction("ridhira_ai_chat_report.action_ai_chat_report_config_settings");
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.submitQuery();
        }
    }
}

export const systrayItem = {
    Component: AiQueryBar,
};

registry.category("systray").add("ridhira_ai_chat_report.AiQueryBar", systrayItem, { sequence: 100 });
registry.category("actions").add("ridhira_ai_chat_report.ai_query_bar", AiReportDashboard);
