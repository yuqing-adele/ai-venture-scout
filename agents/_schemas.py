"""JSON Schema definitions for tool_use structured output"""

CITATION = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "source_name": {"type": "string"},
        "url": {"type": "string"},
        "publish_date": {"type": "string"},
        "confidence": {"type": "string"},
        "retrieval_date": {"type": "string"},
    },
}

DIRECTION_PLANNER = {
    "type": "object",
    "properties": {
        "directions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "rationale": {"type": "string"},
                    "search_keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "category", "rationale", "search_keywords"],
            },
        },
        "excluded_areas": {"type": "array", "items": {"type": "string"}},
        "research_focus": {"type": "string"},
    },
    "required": ["directions", "research_focus"],
}

TECH_SCOUT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "trl_level": {"type": "integer"},
        "trl_rationale": {"type": "string"},
        "paper_volume_trend": {"type": "string"},
        "key_papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "citation_count": {"type": "integer"},
                    "key_finding": {"type": "string"},
                    "source": CITATION,
                },
            },
        },
        "github_activity": {"type": "string"},
        "key_breakthroughs": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "trl_level", "trl_rationale", "paper_volume_trend", "github_activity"],
}

MARKET_AGENT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "market_size_2024_usd_billion": {"type": "number"},
        "cagr_5year_percent": {"type": "number"},
        "growth_drivers": {"type": "array", "items": {"type": "string"}},
        "target_segments": {"type": "array", "items": {"type": "string"}},
        "geographic_focus": {"type": "string"},
        "market_maturity": {"type": "string"},
        "china_market_share_percent": {"type": "number"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "market_size_2024_usd_billion", "cagr_5year_percent"],
}

PATENT_AGENT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "patent_density": {"type": "string"},
        "major_patent_holders": {"type": "array", "items": {"type": "string"}},
        "chinese_patent_holders": {"type": "array", "items": {"type": "string"}},
        "key_patent_areas": {"type": "array", "items": {"type": "string"}},
        "freedom_to_operate_risk": {"type": "string"},
        "risk_rationale": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "patent_density", "freedom_to_operate_risk"],
}

INVESTMENT_AGENT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "investment_heat": {"type": "string"},
        "total_funding_2023_2025_usd_million": {"type": "number"},
        "notable_deals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "amount_usd_million": {"type": "number"},
                    "round": {"type": "string"},
                    "date": {"type": "string"},
                    "investors": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "top_vc_investors": {"type": "array", "items": {"type": "string"}},
        "china_vc_interest": {"type": "string"},
        "investment_stage_focus": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "investment_heat", "total_funding_2023_2025_usd_million"],
}

POLICY_ITEM = {
    "type": "object",
    "properties": {
        "policy_name": {"type": "string"},
        "issuing_body": {"type": "string"},
        "level": {"type": "string"},
        "district": {"type": "string"},
        "key_support": {"type": "string"},
        "benefit_for_startup": {"type": "string"},
    },
}

POLICY_AGENT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "policy_support_level": {"type": "string"},
        "national_policies": {"type": "array", "items": POLICY_ITEM},
        "shenzhen_city_policies": {"type": "array", "items": POLICY_ITEM},
        "district_policies": {"type": "array", "items": POLICY_ITEM},
        "best_district": {"type": "string"},
        "total_subsidy_estimate": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "policy_support_level", "best_district"],
}

COMPETITOR = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "country": {"type": "string"},
        "funding_total_usd_million": {"type": "number"},
        "stage": {"type": "string"},
        "key_product": {"type": "string"},
    },
}

COMPETITOR_AGENT = {
    "type": "object",
    "properties": {
        "direction_name": {"type": "string"},
        "big_tech_players": {"type": "array", "items": {"type": "string"}},
        "big_tech_threat_level": {"type": "string"},
        "startup_competitors": {"type": "array", "items": COMPETITOR},
        "chinese_competitors": {"type": "array", "items": COMPETITOR},
        "market_concentration": {"type": "string"},
        "differentiation_gaps": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["direction_name", "big_tech_threat_level", "market_concentration"],
}

PRODUCT_GENERATOR = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "one_line_description": {"type": "string"},
                    "tech_direction": {"type": "string"},
                    "target_customer": {"type": "string"},
                    "core_value_proposition": {"type": "string"},
                    "why_shenzhen_can_do": {"type": "string"},
                },
                "required": ["id", "name", "one_line_description"],
            },
        },
        "generation_rationale": {"type": "string"},
    },
    "required": ["candidates"],
}

MARKET_DEEP = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "tam_usd_billion": {"type": "number"},
        "sam_usd_billion": {"type": "number"},
        "som_year1_usd_million": {"type": "number"},
        "key_customer_profiles": {"type": "array", "items": {"type": "string"}},
        "sales_channel": {"type": "string"},
        "selling_price_range": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["product_id"],
}

TECH_DEEP = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "core_technologies": {"type": "array", "items": {"type": "string"}},
        "development_timeline_months": {"type": "integer"},
        "team_size_minimum": {"type": "integer"},
        "initial_budget_usd": {"type": "string"},
        "key_technical_risks": {"type": "array", "items": {"type": "string"}},
        "mvp_scope": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["product_id"],
}

COMPETITION_DEEP = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "direct_competitors": {"type": "array", "items": {"type": "string"}},
        "competitive_advantage": {"type": "string"},
        "moat_type": {"type": "string"},
        "entry_barrier": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["product_id"],
}

COMPONENT = {
    "type": "object",
    "properties": {
        "component_name": {"type": "string"},
        "available_on_lcsc": {"type": "boolean"},
        "lcsc_price_usd": {"type": "number"},
        "lead_time_weeks": {"type": "integer"},
        "moq": {"type": "integer"},
        "alternative_sources": {"type": "array", "items": {"type": "string"}},
    },
}

SUPPLY_CHAIN_DEEP = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "key_components": {"type": "array", "items": COMPONENT},
        "bom_cost_estimate_usd": {"type": "string"},
        "local_manufacturer_available": {"type": "boolean"},
        "certifications_needed": {"type": "array", "items": {"type": "string"}},
        "certification_time_months": {"type": "integer"},
        "certification_cost_usd": {"type": "string"},
        "shenzhen_ecosystem_score": {"type": "integer"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["product_id"],
}

POLICY_DEEP = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "best_applicable_policies": {"type": "array", "items": {"type": "string"}},
        "recommended_district": {"type": "string"},
        "estimated_subsidy_usd": {"type": "string"},
        "policy_stability": {"type": "string"},
        "citations": {"type": "array", "items": CITATION},
    },
    "required": ["product_id"],
}
