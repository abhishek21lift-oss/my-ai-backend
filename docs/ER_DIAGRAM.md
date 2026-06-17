# Entity-Relationship Diagram

> Rendered automatically on GitHub via Mermaid. Open in any Mermaid-compatible viewer.

```mermaid
erDiagram

    users {
        UUID    id              PK
        STRING  email           "UNIQUE NOT NULL"
        STRING  display_name
        ENUM    plan            "free | pro | enterprise"
        BOOL    is_active       "DEFAULT true"
        BIGINT  monthly_token_quota
        JSONB   metadata
        TSTZ    created_at
        TSTZ    updated_at
    }

    topics {
        UUID    id              PK
        UUID    user_id         FK
        STRING  name            "NOT NULL"
        TEXT    description
        STRING  category
        BOOL    is_active       "DEFAULT true"
        JSONB   metadata
        TSTZ    created_at
        TSTZ    updated_at
    }

    viral_content {
        UUID    id              PK
        UUID    user_id         FK
        UUID    topic_id        FK "nullable"
        ENUM    platform        "youtube|tiktok|instagram|twitter|linkedin|reddit|other"
        ENUM    content_type    "video|post|article|thread|reel|short"
        TEXT    title           "NOT NULL"
        TEXT    content_url
        BIGINT  views
        BIGINT  likes
        BIGINT  shares
        BIGINT  comments
        FLOAT   engagement_rate
        FLOAT   viral_score     "0–100 CHECK"
        TSTZ    published_at
        TSTZ    collected_at
        JSONB   metadata
        TSTZ    created_at
    }

    trend_analysis {
        UUID    id              PK
        UUID    user_id         FK
        UUID    topic_id        FK "nullable"
        ENUM    period          "daily|weekly|monthly"
        FLOAT   trend_score     "0–100 CHECK"
        ENUM    velocity        "rising|falling|stable|viral"
        JSONB   keywords
        TEXT    insights
        JSONB   data_points
        JSONB   platforms
        TSTZ    analyzed_at
        TSTZ    created_at
    }

    research_reports {
        UUID    id              PK
        UUID    user_id         FK
        UUID    topic_id        FK "nullable"
        STRING  title           "NOT NULL"
        TEXT    summary
        TEXT    content
        JSONB   sources
        JSONB   key_findings
        JSONB   tags
        ENUM    status          "draft|processing|completed|archived"
        INT     word_count
        TSTZ    created_at
        TSTZ    updated_at
    }

    hooks {
        UUID    id              PK
        UUID    user_id         FK
        UUID    topic_id        FK "nullable"
        UUID    viral_content_id FK "nullable"
        ENUM    hook_type       "question|statement|statistic|story|controversy|list|challenge"
        ENUM    platform        "youtube|tiktok|..."
        TEXT    content         "NOT NULL"
        INT     character_count
        FLOAT   quality_score   "0–100 CHECK"
        BOOL    is_used         "DEFAULT false"
        JSONB   metadata
        TSTZ    created_at
    }

    scripts {
        UUID    id              PK
        UUID    user_id         FK
        UUID    topic_id        FK "nullable"
        UUID    hook_id         FK "nullable"
        STRING  title           "NOT NULL"
        ENUM    platform        "youtube|tiktok|..."
        INT     duration_seconds "> 0 CHECK"
        TEXT    content         "NOT NULL"
        JSONB   outline
        INT     word_count      ">= 0 CHECK"
        ENUM    status          "draft|review|approved|published|archived"
        JSONB   metadata
        TSTZ    created_at
        TSTZ    updated_at
    }

    daily_reports {
        UUID    id              PK
        UUID    user_id         FK
        DATE    report_date     "UNIQUE(user_id, report_date)"
        INT     topics_analyzed
        INT     viral_content_collected
        INT     hooks_generated
        INT     scripts_generated
        INT     trends_detected
        INT     reports_generated
        JSONB   top_trends
        JSONB   top_platforms
        TEXT    summary
        BIGINT  tokens_used
        TSTZ    created_at
    }

    agent_logs {
        UUID    id              PK
        UUID    user_id         FK "nullable"
        UUID    parent_log_id   FK "self-ref nullable"
        STRING  agent_name      "NOT NULL"
        STRING  task_type       "NOT NULL"
        ENUM    status          "pending|running|completed|failed|cancelled"
        JSONB   input
        JSONB   output
        TEXT    error
        TEXT    error_traceback
        INT     input_tokens
        INT     output_tokens
        INT     duration_ms
        INT     retry_count
        TSTZ    started_at
        TSTZ    completed_at
        TSTZ    created_at
    }

    analytics {
        UUID    id              PK
        UUID    user_id         FK
        ENUM    entity_type     "topic|viral_content|trend_analysis|research_report|hook|script|daily_report"
        UUID    entity_id       "polymorphic ref"
        ENUM    event_type      "view|create|update|delete|export|copy|share|generate|approve|publish"
        JSONB   metadata
        STRING  ip_address
        TEXT    user_agent
        TSTZ    created_at
    }

    %% ── Relationships ─────────────────────────────────────────────────────

    users           ||--o{    topics              : "owns"
    users           ||--o{    viral_content        : "collects"
    users           ||--o{    trend_analysis       : "generates"
    users           ||--o{    research_reports     : "creates"
    users           ||--o{    hooks                : "generates"
    users           ||--o{    scripts              : "writes"
    users           ||--o{    daily_reports        : "receives"
    users           ||--o{    agent_logs           : "triggers"
    users           ||--o{    analytics            : "tracked in"

    topics          ||--o{    viral_content        : "categorises"
    topics          ||--o{    trend_analysis       : "analysed in"
    topics          ||--o{    research_reports     : "covered by"
    topics          ||--o{    hooks                : "inspires"
    topics          ||--o{    scripts              : "featured in"

    viral_content   ||--o{    hooks                : "inspires"

    hooks           ||--o{    scripts              : "used in"

    agent_logs      |o--o{    agent_logs           : "spawns (sub-tasks)"
```

---

## Index Summary

| Table | Index | Type | Purpose |
|---|---|---|---|
| users | idx_users_email | B-tree | Login lookup |
| users | idx_users_is_active | B-tree | Filter active users |
| users | idx_users_plan | B-tree | Plan-based queries |
| topics | idx_topics_user_id | B-tree | User's topics |
| topics | uq_topics_user_name | Unique | No duplicate names per user |
| viral_content | idx_viral_content_viral_score | B-tree | Sort by virality |
| viral_content | idx_viral_content_user_platform | Composite | Platform filter per user |
| trend_analysis | idx_trend_analysis_velocity | B-tree | Filter rising/viral trends |
| trend_analysis | idx_trend_analysis_user_period | Composite | Period filter per user |
| research_reports | idx_research_reports_active | Partial | Non-archived only |
| hooks | idx_hooks_unused | Partial | Available hooks only |
| hooks | idx_hooks_quality_score | B-tree | Sort by quality |
| scripts | idx_scripts_user_status | Composite | Status filter per user |
| daily_reports | uq_daily_reports_user_date | Unique | One report per user per day |
| agent_logs | idx_agent_logs_failed | Partial | Debug failures fast |
| analytics | idx_analytics_user_entity | Composite | Entity activity per user |
| analytics | idx_analytics_metadata_gin | GIN | JSONB metadata search |

---

## Constraint Summary

| Table | Constraint | Rule |
|---|---|---|
| viral_content | ck_viral_content_viral_score | `0 ≤ viral_score ≤ 100` |
| viral_content | ck_viral_content_views | `views ≥ 0` |
| viral_content | ck_viral_content_likes | `likes ≥ 0` |
| viral_content | ck_viral_content_shares | `shares ≥ 0` |
| viral_content | ck_viral_content_comments | `comments ≥ 0` |
| trend_analysis | ck_trend_analysis_trend_score | `0 ≤ trend_score ≤ 100` |
| hooks | ck_hooks_quality_score | `quality_score IS NULL OR 0–100` |
| scripts | ck_scripts_duration_positive | `duration_seconds IS NULL OR > 0` |
| scripts | ck_scripts_word_count | `word_count IS NULL OR ≥ 0` |
| topics | uq_topics_user_name | `UNIQUE(user_id, name)` |
| daily_reports | uq_daily_reports_user_date | `UNIQUE(user_id, report_date)` |
