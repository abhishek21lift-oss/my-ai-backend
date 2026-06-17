"""
Seed script — populate all tables with realistic development data.

Usage:
    python -m seeds.seed
"""
import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.db import (
    AgentLog,
    AgentStatusEnum,
    Analytics,
    DailyReport,
    EntityTypeEnum,
    EventTypeEnum,
    Hook,
    HookTypeEnum,
    PlatformEnum,
    PlanEnum,
    ReportStatusEnum,
    ResearchReport,
    Script,
    ScriptStatusEnum,
    ContentTypeEnum,
    Topic,
    TrendAnalysis,
    TrendPeriodEnum,
    TrendVelocityEnum,
    User,
    ViralContent,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


async def seed(session: AsyncSession) -> None:
    print("Seeding database...")

    # ── Users ─────────────────────────────────────────────────────────────────
    user_admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        display_name="Admin User",
        plan=PlanEnum.enterprise,
        is_active=True,
        monthly_token_quota=10_000_000,
    )
    user_pro = User(
        id=uuid.uuid4(),
        email="pro@example.com",
        display_name="Pro Creator",
        plan=PlanEnum.pro,
        is_active=True,
        monthly_token_quota=2_000_000,
    )
    user_free = User(
        id=uuid.uuid4(),
        email="free@example.com",
        display_name="Free Tier User",
        plan=PlanEnum.free,
        is_active=True,
        monthly_token_quota=100_000,
    )
    session.add_all([user_admin, user_pro, user_free])
    await session.flush()
    print(f"  ✓ 3 users created")

    # ── Topics ────────────────────────────────────────────────────────────────
    topic_data = [
        ("AI & Machine Learning", "artificial-intelligence"),
        ("Personal Finance", "finance"),
        ("Fitness & Health", "health"),
        ("Entrepreneurship", "business"),
        ("Social Media Growth", "social-media"),
    ]
    topics = []
    for name, category in topic_data:
        t = Topic(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            name=name,
            description=f"Trending content about {name}",
            category=category,
            is_active=True,
        )
        topics.append(t)
        session.add(t)

    topic_pro = Topic(
        id=uuid.uuid4(),
        user_id=user_pro.id,
        name="Content Creation",
        category="social-media",
        is_active=True,
    )
    session.add(topic_pro)
    await session.flush()
    print(f"  ✓ {len(topics) + 1} topics created")

    # ── Viral Content ─────────────────────────────────────────────────────────
    viral_items = [
        ViralContent(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[0].id,
            platform=PlatformEnum.youtube,
            content_type=ContentTypeEnum.video,
            title="I trained an AI model with $0 in 2025 — here's what happened",
            content_url="https://youtube.com/watch?v=example1",
            views=2_400_000,
            likes=89_000,
            shares=34_000,
            comments=12_500,
            engagement_rate=5.7,
            viral_score=92.3,
            published_at=_days_ago(3),
        ),
        ViralContent(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[1].id,
            platform=PlatformEnum.tiktok,
            content_type=ContentTypeEnum.short,
            title="The 50/30/20 rule changed my life — watch this",
            content_url="https://tiktok.com/@example/video/2",
            views=5_100_000,
            likes=620_000,
            shares=180_000,
            comments=42_000,
            engagement_rate=16.5,
            viral_score=97.8,
            published_at=_days_ago(1),
        ),
        ViralContent(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[2].id,
            platform=PlatformEnum.instagram,
            content_type=ContentTypeEnum.reel,
            title="7-minute morning routine that 10x'd my productivity",
            content_url="https://instagram.com/reel/example3",
            views=890_000,
            likes=74_000,
            shares=22_000,
            comments=8_200,
            engagement_rate=11.7,
            viral_score=85.4,
            published_at=_days_ago(5),
        ),
        ViralContent(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[3].id,
            platform=PlatformEnum.linkedin,
            content_type=ContentTypeEnum.post,
            title="I quit my $300k job to build a startup. 18 months later...",
            content_url="https://linkedin.com/posts/example4",
            views=340_000,
            likes=28_500,
            shares=9_700,
            comments=3_100,
            engagement_rate=12.1,
            viral_score=88.9,
            published_at=_days_ago(7),
        ),
        ViralContent(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[4].id,
            platform=PlatformEnum.twitter,
            content_type=ContentTypeEnum.thread,
            title="10 growth hacks that took my account from 0 to 100k followers",
            content_url="https://twitter.com/example/status/5",
            views=780_000,
            likes=42_000,
            shares=18_500,
            comments=6_400,
            engagement_rate=8.6,
            viral_score=79.2,
            published_at=_days_ago(2),
        ),
    ]
    session.add_all(viral_items)
    await session.flush()
    print(f"  ✓ {len(viral_items)} viral content items created")

    # ── Trend Analysis ────────────────────────────────────────────────────────
    trend_items = [
        TrendAnalysis(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[0].id,
            period=TrendPeriodEnum.weekly,
            trend_score=94.5,
            velocity=TrendVelocityEnum.viral,
            keywords=["ChatGPT", "Claude", "Gemini", "AI tools", "automation"],
            insights=(
                "AI tools content is experiencing a viral surge. "
                "Short-form tutorials outperform long-form by 3x this week."
            ),
            data_points=[
                {"date": str(_days_ago(6).date()), "score": 78.0},
                {"date": str(_days_ago(5).date()), "score": 81.2},
                {"date": str(_days_ago(4).date()), "score": 85.6},
                {"date": str(_days_ago(3).date()), "score": 88.9},
                {"date": str(_days_ago(2).date()), "score": 91.3},
                {"date": str(_days_ago(1).date()), "score": 94.5},
            ],
            platforms=["youtube", "tiktok", "twitter"],
        ),
        TrendAnalysis(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[1].id,
            period=TrendPeriodEnum.daily,
            trend_score=88.1,
            velocity=TrendVelocityEnum.rising,
            keywords=["passive income", "investing", "index funds", "crypto", "side hustle"],
            insights="Personal finance content peaks on Monday mornings and Friday afternoons.",
            data_points=[{"hour": h, "score": 60 + h * 2.5} for h in range(24)],
            platforms=["tiktok", "youtube", "instagram"],
        ),
        TrendAnalysis(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[2].id,
            period=TrendPeriodEnum.monthly,
            trend_score=72.3,
            velocity=TrendVelocityEnum.stable,
            keywords=["morning routine", "workout", "meal prep", "mental health", "sleep"],
            insights="Health content stable month-over-month. Niche down to mental health for higher engagement.",
            data_points=[{"week": w, "score": 68 + w * 1.5} for w in range(4)],
            platforms=["instagram", "tiktok", "youtube"],
        ),
    ]
    session.add_all(trend_items)
    await session.flush()
    print(f"  ✓ {len(trend_items)} trend analyses created")

    # ── Research Reports ──────────────────────────────────────────────────────
    reports = [
        ResearchReport(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[0].id,
            title="State of AI Content Creation: Q2 2026",
            summary=(
                "AI-generated and AI-assisted content has reached 34% of all viral posts "
                "across major platforms. Audiences respond 2.4x better to human-narrated AI explainers."
            ),
            content=(
                "## Executive Summary\n\nAI content is mainstream. Creators who transparently "
                "disclose AI assistance see higher trust scores...\n\n## Key Findings\n\n"
                "1. Short-form AI tutorials outperform long-form by 312%\n"
                "2. TikTok's algorithm favors AI tool demos in the 60–90s range\n"
                "3. LinkedIn audiences prefer case studies over tutorials for AI topics"
            ),
            sources=[
                {"title": "Pew Research AI Report 2026", "url": "https://example.com/pew"},
                {"title": "Creator Economy Trends", "url": "https://example.com/creator"},
            ],
            key_findings=[
                "Short-form AI tutorials outperform long-form by 312%",
                "TikTok favors AI tool demos in 60–90s range",
                "LinkedIn audiences prefer case studies for AI topics",
            ],
            tags=["ai", "content-creation", "trends", "q2-2026"],
            status=ReportStatusEnum.completed,
            word_count=3_420,
        ),
        ResearchReport(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[3].id,
            title="Entrepreneurship Content: What Actually Goes Viral in 2026",
            summary="Failure stories outperform success stories 4:1 in engagement metrics.",
            content="## Analysis\n\nCounterintuitively, founders who share failures...",
            sources=[
                {"title": "Founder Survey 2026", "url": "https://example.com/founder"},
            ],
            key_findings=[
                "Failure stories get 4x more engagement than success stories",
                "Revenue reveal posts drive the highest follower conversion",
            ],
            tags=["entrepreneurship", "startup", "viral"],
            status=ReportStatusEnum.completed,
            word_count=2_180,
        ),
        ResearchReport(
            id=uuid.uuid4(),
            user_id=user_pro.id,
            topic_id=topic_pro.id,
            title="Optimal Posting Frequency by Platform — June 2026",
            summary="Draft analysis of optimal posting cadence across 7 platforms.",
            status=ReportStatusEnum.draft,
            tags=["posting-strategy", "social-media"],
            word_count=0,
        ),
    ]
    session.add_all(reports)
    await session.flush()
    print(f"  ✓ {len(reports)} research reports created")

    # ── Hooks ─────────────────────────────────────────────────────────────────
    hooks = [
        Hook(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[0].id,
            viral_content_id=viral_items[0].id,
            hook_type=HookTypeEnum.question,
            platform=PlatformEnum.youtube,
            content="What if you could build an AI product in 24 hours without writing a single line of code?",
            character_count=88,
            quality_score=91.5,
            is_used=False,
        ),
        Hook(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[1].id,
            viral_content_id=viral_items[1].id,
            hook_type=HookTypeEnum.statistic,
            platform=PlatformEnum.tiktok,
            content="93% of people will never retire comfortably — and 3 decisions make all the difference.",
            character_count=95,
            quality_score=96.2,
            is_used=True,
        ),
        Hook(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[2].id,
            hook_type=HookTypeEnum.story,
            platform=PlatformEnum.instagram,
            content="I used to hit snooze 7 times every morning. One habit changed everything.",
            character_count=74,
            quality_score=87.8,
            is_used=False,
        ),
        Hook(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[3].id,
            viral_content_id=viral_items[3].id,
            hook_type=HookTypeEnum.controversy,
            platform=PlatformEnum.linkedin,
            content="Hustle culture is killing your startup. Here's the data to prove it.",
            character_count=69,
            quality_score=89.0,
            is_used=False,
        ),
        Hook(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[4].id,
            viral_content_id=viral_items[4].id,
            hook_type=HookTypeEnum.list_,
            platform=PlatformEnum.twitter,
            content="5 platform algorithm changes in the last 30 days that are crushing organic reach (thread):",
            character_count=93,
            quality_score=82.4,
            is_used=False,
        ),
        Hook(
            id=uuid.uuid4(),
            user_id=user_pro.id,
            topic_id=topic_pro.id,
            hook_type=HookTypeEnum.challenge,
            platform=PlatformEnum.tiktok,
            content="Post every day for 30 days with these exact templates — I'll show you the results.",
            character_count=85,
            quality_score=79.6,
            is_used=False,
        ),
    ]
    session.add_all(hooks)
    await session.flush()
    print(f"  ✓ {len(hooks)} hooks created")

    # ── Scripts ───────────────────────────────────────────────────────────────
    scripts = [
        Script(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[0].id,
            hook_id=hooks[0].id,
            title="How I Built an AI Product in 24 Hours (No Code)",
            platform=PlatformEnum.youtube,
            duration_seconds=480,
            content=(
                "[HOOK] What if you could build an AI product in 24 hours without writing "
                "a single line of code?\n\n"
                "[INTRO] Hey, I'm [Name], and today I'm going to show you exactly how I "
                "built a fully functional AI tool using only no-code platforms...\n\n"
                "[MAIN CONTENT]\n1. Choosing your AI use case (2 min)\n"
                "2. Setting up the workflow in Make.com (8 min)\n"
                "3. Connecting to the Claude API (5 min)\n"
                "4. Building the frontend with Framer (4 min)\n"
                "5. Testing and launch (3 min)\n\n"
                "[CTA] Subscribe for my weekly AI build videos and drop a comment with "
                "what you want to build next!"
            ),
            outline=[
                {"section": "Hook", "duration": 15, "notes": "Pattern interrupt"},
                {"section": "Intro", "duration": 30, "notes": "Establish credibility"},
                {"section": "Use Case", "duration": 120, "notes": "Show the problem"},
                {"section": "Make.com Setup", "duration": 480, "notes": "Screen record"},
                {"section": "Claude API", "duration": 300, "notes": "Show API calls"},
                {"section": "Frontend", "duration": 240, "notes": "Framer tutorial"},
                {"section": "CTA", "duration": 30, "notes": "Subscribe + comment"},
            ],
            word_count=312,
            status=ScriptStatusEnum.approved,
        ),
        Script(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            topic_id=topics[1].id,
            hook_id=hooks[1].id,
            title="3 Money Decisions That Separate the Top 7% (TikTok)",
            platform=PlatformEnum.tiktok,
            duration_seconds=75,
            content=(
                "93% of people will never retire comfortably — and 3 decisions make all the difference.\n\n"
                "Decision 1: Start before you're ready. [Cut to chart showing compound interest]\n"
                "Decision 2: Automate, don't willpower. Set up auto-invest on payday.\n"
                "Decision 3: Index over picking stocks. The data is clear.\n\n"
                "If this helped, follow for more finance tips every week."
            ),
            outline=[
                {"section": "Hook stat", "duration": 5},
                {"section": "Decision 1", "duration": 20},
                {"section": "Decision 2", "duration": 20},
                {"section": "Decision 3", "duration": 20},
                {"section": "CTA", "duration": 10},
            ],
            word_count=89,
            status=ScriptStatusEnum.published,
        ),
        Script(
            id=uuid.uuid4(),
            user_id=user_pro.id,
            topic_id=topic_pro.id,
            hook_id=hooks[5].id,
            title="30-Day Posting Challenge — Day 1",
            platform=PlatformEnum.tiktok,
            duration_seconds=60,
            content="Starting a 30-day challenge today. Here's my exact posting template...",
            word_count=45,
            status=ScriptStatusEnum.draft,
        ),
    ]
    session.add_all(scripts)
    await session.flush()
    print(f"  ✓ {len(scripts)} scripts created")

    # ── Daily Reports ─────────────────────────────────────────────────────────
    daily_reports = []
    for i in range(7):
        dr = DailyReport(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            report_date=date.today() - timedelta(days=i),
            topics_analyzed=5,
            viral_content_collected=12 + i,
            hooks_generated=8 - i,
            scripts_generated=3,
            trends_detected=4,
            reports_generated=1 if i == 0 else 0,
            top_trends=[
                {"topic": "AI & Machine Learning", "score": 94.5},
                {"topic": "Personal Finance", "score": 88.1},
                {"topic": "Entrepreneurship", "score": 76.3},
            ],
            top_platforms=[
                {"platform": "tiktok", "content_count": 5},
                {"platform": "youtube", "content_count": 4},
                {"platform": "instagram", "content_count": 3},
            ],
            summary=(
                f"Strong day for AI and finance content. {12 + i} viral pieces collected. "
                f"TikTok continues to dominate engagement metrics."
            ),
            tokens_used=45_230 + (i * 1_200),
        )
        daily_reports.append(dr)
        session.add(dr)
    await session.flush()
    print(f"  ✓ {len(daily_reports)} daily reports created")

    # ── Agent Logs ────────────────────────────────────────────────────────────
    agent_logs = [
        AgentLog(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            agent_name="TrendResearchAgent",
            task_type="trend_analysis",
            status=AgentStatusEnum.completed,
            input={"topic_id": str(topics[0].id), "period": "weekly"},
            output={"trend_score": 94.5, "velocity": "viral", "keywords_found": 12},
            input_tokens=1_240,
            output_tokens=820,
            duration_ms=3_450,
            retry_count=0,
            started_at=_days_ago(1),
            completed_at=_days_ago(1) + timedelta(seconds=3),
        ),
        AgentLog(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            agent_name="ContentScraperAgent",
            task_type="viral_content_collection",
            status=AgentStatusEnum.completed,
            input={"platforms": ["tiktok", "youtube"], "limit": 20},
            output={"items_collected": 18, "avg_viral_score": 76.4},
            input_tokens=540,
            output_tokens=2_100,
            duration_ms=8_920,
            retry_count=0,
            started_at=_days_ago(0),
            completed_at=_days_ago(0) + timedelta(seconds=9),
        ),
        AgentLog(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            agent_name="HookGeneratorAgent",
            task_type="hook_generation",
            status=AgentStatusEnum.completed,
            input={
                "topic_id": str(topics[1].id),
                "platform": "tiktok",
                "count": 5,
            },
            output={"hooks_generated": 5, "avg_quality_score": 88.3},
            input_tokens=980,
            output_tokens=1_450,
            duration_ms=4_210,
            retry_count=0,
            started_at=_days_ago(0),
            completed_at=_days_ago(0) + timedelta(seconds=4),
        ),
        AgentLog(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            agent_name="ScriptWriterAgent",
            task_type="script_generation",
            status=AgentStatusEnum.failed,
            input={"hook_id": str(hooks[2].id), "platform": "instagram"},
            error="Rate limit exceeded on Anthropic API",
            error_traceback="anthropic.RateLimitError: 429 Too Many Requests\n  ...",
            input_tokens=420,
            output_tokens=0,
            duration_ms=1_200,
            retry_count=2,
            started_at=_days_ago(0),
            completed_at=_days_ago(0) + timedelta(seconds=1),
        ),
        AgentLog(
            id=uuid.uuid4(),
            user_id=user_pro.id,
            agent_name="DailyReportAgent",
            task_type="daily_report_generation",
            status=AgentStatusEnum.running,
            input={"user_id": str(user_pro.id), "date": str(date.today())},
            input_tokens=0,
            output_tokens=0,
            retry_count=0,
            started_at=_now(),
        ),
    ]
    session.add_all(agent_logs)
    await session.flush()
    print(f"  ✓ {len(agent_logs)} agent logs created")

    # ── Analytics ─────────────────────────────────────────────────────────────
    analytics_events = []

    # Topic view events
    for topic in topics[:3]:
        for _ in range(5):
            analytics_events.append(Analytics(
                id=uuid.uuid4(),
                user_id=user_admin.id,
                entity_type=EntityTypeEnum.topic,
                entity_id=topic.id,
                event_type=EventTypeEnum.view,
                metadata_={"source": "dashboard"},
            ))

    # Hook generate + copy events
    for hook in hooks[:4]:
        analytics_events.append(Analytics(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            entity_type=EntityTypeEnum.hook,
            entity_id=hook.id,
            event_type=EventTypeEnum.generate,
            metadata_={"agent": "HookGeneratorAgent"},
        ))
        analytics_events.append(Analytics(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            entity_type=EntityTypeEnum.hook,
            entity_id=hook.id,
            event_type=EventTypeEnum.copy,
            metadata_={"platform": hook.platform.value},
        ))

    # Script create + approve events
    for script in scripts[:2]:
        analytics_events.append(Analytics(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            entity_type=EntityTypeEnum.script,
            entity_id=script.id,
            event_type=EventTypeEnum.create,
            metadata_={"platform": script.platform.value},
        ))
        analytics_events.append(Analytics(
            id=uuid.uuid4(),
            user_id=user_admin.id,
            entity_type=EntityTypeEnum.script,
            entity_id=script.id,
            event_type=EventTypeEnum.approve,
            metadata_={},
        ))

    # Research report export
    analytics_events.append(Analytics(
        id=uuid.uuid4(),
        user_id=user_admin.id,
        entity_type=EntityTypeEnum.research_report,
        entity_id=reports[0].id,
        event_type=EventTypeEnum.export,
        metadata_={"format": "pdf"},
    ))

    session.add_all(analytics_events)
    await session.flush()
    print(f"  ✓ {len(analytics_events)} analytics events created")

    await session.commit()
    print("\n✅ Seed complete.")
    print(f"   Users:            3")
    print(f"   Topics:           {len(topics) + 1}")
    print(f"   Viral Content:    {len(viral_items)}")
    print(f"   Trend Analyses:   {len(trend_items)}")
    print(f"   Research Reports: {len(reports)}")
    print(f"   Hooks:            {len(hooks)}")
    print(f"   Scripts:          {len(scripts)}")
    print(f"   Daily Reports:    {len(daily_reports)}")
    print(f"   Agent Logs:       {len(agent_logs)}")
    print(f"   Analytics Events: {len(analytics_events)}")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
