/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

/**
 * Helper to initialize browser Web Speech Recognition for voice queries
 */
function createSpeechRecognizer(onResult, onEnd, onError) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = navigator.language || "en-US";

        recognition.onresult = (event) => {
            if (event.results && event.results[0] && event.results[0][0]) {
                const transcript = event.results[0][0].transcript;
                onResult(transcript);
            }
        };

        recognition.onerror = (event) => {
            if (onError) onError(event.error);
        };

        recognition.onend = () => {
            if (onEnd) onEnd();
        };

        return recognition;
    } catch (e) {
        return null;
    }
}

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
            refinePrompt: "",
            isLoading: false,
            isListening: false,
            error: null,
            activeResult: null, // Holds { query_id, model_name, chart_type, ai_insight, ... }
            isRefineMode: false,
        });

        this.suggestions = [
            "Top 5 customers by sales (bar chart)",
            "Sales by month as a stacked bar",
            "Invoices by status as a pie chart",
            "Active leads grouped by stage",
            "Active users grouped by company (pivot table)",
        ];

        this.recognizer = null;

        onWillUnmount(() => {
            if (this.recognizer) {
                try {
                    this.recognizer.stop();
                } catch (e) {}
            }
        });
    }

    togglePanel() {
        this.state.isOpen = !this.state.isOpen;
        this.state.error = null;
    }

    closePanel() {
        this.state.isOpen = false;
        this.state.error = null;
        if (this.state.isListening && this.recognizer) {
            try { this.recognizer.stop(); } catch (e) {}
            this.state.isListening = false;
        }
    }

    setPrompt(suggestion) {
        this.state.prompt = suggestion;
        this.state.isRefineMode = false;
    }

    toggleVoiceInput() {
        if (this.state.isListening) {
            if (this.recognizer) {
                try { this.recognizer.stop(); } catch (e) {}
            }
            this.state.isListening = false;
            return;
        }

        this.recognizer = createSpeechRecognizer(
            (transcript) => {
                this.state.prompt = (this.state.prompt ? this.state.prompt + " " : "") + transcript;
                this.state.isListening = false;
                this.notification.add("Voice prompt captured!", { type: "info" });
            },
            () => {
                this.state.isListening = false;
            },
            (error) => {
                this.state.isListening = false;
                if (error !== "no-speech") {
                    this.notification.add(`Speech recognition error: ${error}`, { type: "warning" });
                }
            }
        );

        if (!this.recognizer) {
            this.notification.add("Speech Recognition is not supported by this browser. Please type your query.", {
                type: "warning",
            });
            return;
        }

        try {
            this.state.isListening = true;
            this.recognizer.start();
        } catch (e) {
            this.state.isListening = false;
        }
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

            this.state.activeResult = response;
            this.state.isRefineMode = true;
            this.state.refinePrompt = "";

            if (response.action) {
                await this.action.doAction(response.action);
            }
        } catch (error) {
            this.state.error = error.message || (error.data && error.data.message) || "Failed to generate AI report.";
            console.error("AI Report Error:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async submitRefinement(refineText) {
        const text = refineText || this.state.refinePrompt.trim();
        if (!text || !this.state.activeResult || !this.state.activeResult.query_id) return;

        this.state.isLoading = true;
        this.state.error = null;

        try {
            const response = await this.orm.call(
                "ai.report.query",
                "action_refine_query",
                [this.state.activeResult.query_id, text]
            );

            this.state.activeResult = response;
            this.state.refinePrompt = "";

            if (response.action) {
                await this.action.doAction(response.action);
            }
        } catch (error) {
            this.state.error = error.message || (error.data && error.data.message) || "Failed to refine report.";
            console.error("AI Refine Error:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    resetQuery() {
        this.state.activeResult = null;
        this.state.isRefineMode = false;
        this.state.prompt = "";
        this.state.refinePrompt = "";
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            if (this.state.isRefineMode) {
                this.submitRefinement();
            } else {
                this.submitQuery();
            }
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
            refinePrompt: "",
            isLoading: false,
            isListening: false,
            error: null,
            activeResult: null,
            isRefineMode: false,
            recentQueries: [],
            activeTab: "explore", // 'explore' or 'history'
        });

        this.categories = [
            {
                title: "Sales & Revenue",
                icon: "fa-line-chart",
                color: "text-primary",
                queries: [
                    "Show sales by customer as a bar chart",
                    "Monthly sales comparison as a line chart",
                    "Top 10 selling products this quarter",
                    "Sales volume by salesperson as stacked bar",
                ]
            },
            {
                title: "Invoicing & Financials",
                icon: "fa-file-text-o",
                color: "text-success",
                queries: [
                    "Customer invoices grouped by payment state",
                    "Total expenses by category as a pie chart",
                    "Monthly revenue breakdown in pivot table",
                    "Overdue receivables by partner",
                ]
            },
            {
                title: "CRM & Pipelines",
                icon: "fa-users",
                color: "text-warning",
                queries: [
                    "Opportunity pipeline grouped by stage",
                    "Expected revenue by salesperson",
                    "Leads created in last 30 days by medium",
                    "Win rate by campaign in pivot table",
                ]
            },
            {
                title: "Inventory & Operations",
                icon: "fa-cubes",
                color: "text-info",
                queries: [
                    "Stock transfers grouped by operation type",
                    "Purchase orders by vendor as a bar chart",
                    "Late deliveries pending this week",
                    "Inventory valuation by product category",
                ]
            }
        ];

        this.recognizer = null;

        onMounted(() => {
            this.loadRecentQueries();
        });

        onWillUnmount(() => {
            if (this.recognizer) {
                try { this.recognizer.stop(); } catch (e) {}
            }
        });
    }

    async loadRecentQueries() {
        try {
            const records = await this.orm.searchRead(
                "ai.report.query",
                [],
                ["name", "user_prompt", "model_name", "chart_type", "measure", "ai_insight", "is_favorite", "create_date"],
                { limit: 10, order: "is_favorite desc, id desc" }
            );
            this.state.recentQueries = records;
        } catch (e) {
            this.state.recentQueries = [];
        }
    }

    setPrompt(query) {
        this.state.prompt = query;
        this.state.isRefineMode = false;
        this.state.activeResult = null;
    }

    toggleVoiceInput() {
        if (this.state.isListening) {
            if (this.recognizer) {
                try { this.recognizer.stop(); } catch (e) {}
            }
            this.state.isListening = false;
            return;
        }

        this.recognizer = createSpeechRecognizer(
            (transcript) => {
                this.state.prompt = (this.state.prompt ? this.state.prompt + " " : "") + transcript;
                this.state.isListening = false;
                this.notification.add("Voice prompt captured!", { type: "info" });
            },
            () => {
                this.state.isListening = false;
            },
            (error) => {
                this.state.isListening = false;
                if (error !== "no-speech") {
                    this.notification.add(`Speech recognition error: ${error}`, { type: "warning" });
                }
            }
        );

        if (!this.recognizer) {
            this.notification.add("Speech Recognition is not supported by your browser.", { type: "warning" });
            return;
        }

        try {
            this.state.isListening = true;
            this.recognizer.start();
        } catch (e) {
            this.state.isListening = false;
        }
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

            this.state.activeResult = response;
            this.state.isRefineMode = true;
            this.state.refinePrompt = "";
            this.loadRecentQueries();

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

    async submitRefinement(refineText) {
        const text = refineText || this.state.refinePrompt.trim();
        if (!text || !this.state.activeResult || !this.state.activeResult.query_id) return;

        this.state.isLoading = true;
        this.state.error = null;

        try {
            const response = await this.orm.call(
                "ai.report.query",
                "action_refine_query",
                [this.state.activeResult.query_id, text]
            );

            this.state.activeResult = response;
            this.state.refinePrompt = "";
            this.loadRecentQueries();

            if (response.action) {
                await this.action.doAction(response.action);
            }
        } catch (error) {
            this.state.error = error.message || (error.data && error.data.message) || "Failed to refine report.";
            console.error(error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async toggleFavorite(record, ev) {
        if (ev) ev.stopPropagation();
        try {
            await this.orm.call("ai.report.query", "action_toggle_favorite", [[record.id]]);
            record.is_favorite = !record.is_favorite;
        } catch (e) {
            console.error(e);
        }
    }

    async runRecentQuery(record) {
        this.state.prompt = record.user_prompt;
        this.state.isRefineMode = false;
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
            if (this.state.isRefineMode) {
                this.submitRefinement();
            } else {
                this.submitQuery();
            }
        }
    }
}

export const systrayItem = {
    Component: AiQueryBar,
};

registry.category("systray").add("ridhira_ai_chat_report.AiQueryBar", systrayItem, { sequence: 100 });
registry.category("actions").add("ridhira_ai_chat_report.ai_query_bar", AiReportDashboard);
