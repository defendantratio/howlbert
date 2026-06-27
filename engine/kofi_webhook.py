"""HTTP listener for Ko-fi donation webhooks."""

from __future__ import annotations

import json
import logging

from aiohttp import web

from config import KOFI_VERIFICATION_TOKEN, KOFI_WEBHOOK_PORT
from engine.donor import process_kofi_event

logger = logging.getLogger("howlbert.kofi")

_runner: web.AppRunner | None = None


async def _handle_kofi(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    payload: dict | None = None

    if request.content_type == "application/json":
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            return web.Response(text="bad json", status=400)
    else:
        post = await request.post()
        raw = post.get("data")
        if raw:
            try:
                payload = json.loads(str(raw))
            except json.JSONDecodeError:
                return web.Response(text="bad data field", status=400)

    if not payload:
        return web.Response(text="missing payload", status=400)

    ok, note, discord_id, dm_message = process_kofi_event(
        payload, expected_token=KOFI_VERIFICATION_TOKEN
    )

    if ok:
        event_type = str(payload.get("type", "Donation"))
        is_sub = payload.get("is_subscription_payment") or event_type == "Subscription"
        is_shop = event_type == "Shop Order"
        logger.info(
            "Ko-fi %s processed: %s (discord_id=%s)",
            "shop" if is_shop else ("membership" if is_sub else "payment"),
            note,
            discord_id,
        )
        if discord_id and bot:
            user = await bot.fetch_user(discord_id)
            if user:
                try:
                    if dm_message:
                        body = dm_message
                    elif is_shop:
                        body = f"**thank you for your shop order!** 🦴\n{note}"
                    elif is_sub:
                        body = (
                            f"**thank you for your membership!** 🦴\n{note}\n"
                            "check `/patron` for your donor status."
                        )
                    else:
                        body = (
                            f"**thank you for supporting the den!** 🦴\n{note}\n"
                            "check `/patron` for your donor status."
                        )
                    await user.send(body)
                except Exception:
                    logger.debug("Could not DM donor %s", discord_id, exc_info=True)
        return web.Response(text="ok")
    logger.warning("ko-fi rejected: %s", note)
    return web.Response(text=note, status=400)


async def start_kofi_webhook(bot) -> None:
    global _runner
    if not KOFI_VERIFICATION_TOKEN:
        logger.info("KOFI_VERIFICATION_TOKEN unset; Ko-fi webhook disabled.")
        return
    if _runner is not None:
        return

    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/kofi", _handle_kofi)
    app.router.add_get("/kofi/health", lambda _r: web.Response(text="ok"))

    runner = web.AppRunner(app)
    try:
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", KOFI_WEBHOOK_PORT)
        await site.start()
    except OSError as exc:
        await runner.cleanup()
        if exc.errno in {48, 98, 10048}:  # EADDRINUSE (mac/linux/windows)
            logger.warning(
                "Ko-fi webhook port %s already in use; webhook disabled for this "
                "instance. Stop the other bot process or set KOFI_WEBHOOK_PORT in .env.",
                KOFI_WEBHOOK_PORT,
            )
            return
        raise
    _runner = runner
    logger.info("ko-fi webhook listening on port %s (post /kofi)", KOFI_WEBHOOK_PORT)


async def stop_kofi_webhook() -> None:
    global _runner
    if _runner is None:
        return
    await _runner.cleanup()
    _runner = None
