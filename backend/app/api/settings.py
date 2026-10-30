import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import ApiConfig
from ..schemas import ApiConfigOut, ApiConfigUpdate, ApiTestRequest, ApiTestResponse
from ..engine.adapters import (
    TavilyAdapter, GoogleSearchAdapter, GooglePlacesAdapter,
    BingAdapter, BraveAdapter, ApolloAdapter, HunterAdapter
)

router = APIRouter(prefix="/api/settings", tags=["API Settings"])

SUPPORTED_PROVIDERS = [
    "Gemini", "OpenAI", "Tavily", "Google Places", 
    "Google Search", "Bing", "Brave", "Apollo", "Hunter"
]

@router.get("", response_model=list[ApiConfigOut])
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """
    Returns list of all supported API providers and their configuration status.
    """
    res = await db.execute(select(ApiConfig))
    existing = {cfg.provider_name.lower(): cfg for cfg in res.scalars().all()}

    output = []
    for prov in SUPPORTED_PROVIDERS:
        key = prov.lower().replace(" ", "_")
        cfg = existing.get(key)
        if cfg:
            output.append(ApiConfigOut(
                id=cfg.id,
                provider_name=prov,
                is_enabled=cfg.is_enabled,
                is_connected=cfg.is_connected,
                last_tested=cfg.last_tested,
                last_error=cfg.last_error or "",
                usage_count=cfg.usage_count,
                has_key=bool(cfg.api_key.strip())
            ))
        else:
            output.append(ApiConfigOut(
                id=key,
                provider_name=prov,
                is_enabled=True,
                is_connected=False,
                last_tested=None,
                last_error="",
                usage_count=0,
                has_key=False
            ))
    return output

@router.post("", response_model=ApiConfigOut)
async def save_setting(req: ApiConfigUpdate, db: AsyncSession = Depends(get_db)):
    """
    Saves or updates API credentials securely.
    """
    key = req.provider_name.lower().replace(" ", "_")
    res = await db.execute(select(ApiConfig).where(ApiConfig.provider_name == key))
    cfg = res.scalars().first()

    if not cfg:
        cfg = ApiConfig(provider_name=key)
        db.add(cfg)

    cfg.api_key = req.api_key.strip()
    cfg.is_enabled = req.is_enabled
    if req.extra_config:
        cfg.extra_config = json.dumps(req.extra_config)
    
    # Reset connection flag until tested
    cfg.is_connected = False
    await db.commit()
    await db.refresh(cfg)

    return ApiConfigOut(
        id=cfg.id,
        provider_name=req.provider_name,
        is_enabled=cfg.is_enabled,
        is_connected=cfg.is_connected,
        last_tested=cfg.last_tested,
        last_error=cfg.last_error or "",
        usage_count=cfg.usage_count,
        has_key=bool(cfg.api_key)
    )

@router.post("/test", response_model=ApiTestResponse)
async def test_provider_connection(req: ApiTestRequest, db: AsyncSession = Depends(get_db)):
    """
    Performs a live test of an API provider connection.
    """
    key = req.provider_name.lower().replace(" ", "_")
    
    api_key = req.api_key
    extra = req.extra_config or {}

    # If key not provided in body, load from DB
    if not api_key:
        res = await db.execute(select(ApiConfig).where(ApiConfig.provider_name == key))
        cfg = res.scalars().first()
        if cfg:
            api_key = cfg.api_key
            if not extra and cfg.extra_config:
                extra = json.loads(cfg.extra_config)

    if not api_key:
        return ApiTestResponse(
            provider_name=req.provider_name,
            success=False,
            message="No API key provided or configured."
        )

    success = False
    msg = ""

    # Test based on provider
    try:
        if key == "tavily":
            adapter = TavilyAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "google_search":
            adapter = GoogleSearchAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "google_places":
            adapter = GooglePlacesAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "bing":
            adapter = BingAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "brave":
            adapter = BraveAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "apollo":
            adapter = ApolloAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "hunter":
            adapter = HunterAdapter(api_key=api_key, extra_config=extra)
            success, msg = await adapter.test_connection()
        elif key == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents="Ping",
            )
            success = bool(resp and resp.text)
            msg = "Gemini API connection verified successfully!"
        elif key == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            models = await client.models.list()
            success = bool(models and models.data)
            msg = "OpenAI API connection verified successfully!"
        else:
            success = False
            msg = f"Unknown provider: {req.provider_name}"
    except Exception as e:
        success = False
        msg = f"Connection error: {str(e)}"

    # Update DB config state if exists
    res = await db.execute(select(ApiConfig).where(ApiConfig.provider_name == key))
    cfg = res.scalars().first()
    if cfg:
        cfg.is_connected = success
        cfg.last_tested = datetime.utcnow()
        cfg.last_error = "" if success else msg
        await db.commit()

    return ApiTestResponse(
        provider_name=req.provider_name,
        success=success,
        message=msg
    )
