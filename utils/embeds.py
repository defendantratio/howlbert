import discord

from config import BOT_DISPLAY_NAME

EMBED_COLOR = discord.Color.from_rgb(139, 119, 90)  # warm fur brown
SUCCESS_COLOR = discord.Color.from_rgb(107, 142, 90)
ERROR_COLOR = discord.Color.from_rgb(160, 82, 72)


def embed_footer(*extra: str) -> str:
    """Standard Howlbert footer; optional suffix segments."""
    base = f"{BOT_DISPLAY_NAME} · Wolf RP"
    if not extra:
        return base
    return f"{base} · {' · '.join(extra)}"


def howlbert_embed(title: str, description: str = "", *, color=EMBED_COLOR) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=embed_footer())
    return embed


def trim_embed_fields(embed: discord.Embed, max_fields: int = 25) -> discord.Embed:
    """Fold overflow fields into one block so Discord accepts the embed (max 25 fields)."""
    if len(embed.fields) <= max_fields:
        return embed
    keep = embed.fields[: max_fields - 1]
    overflow = embed.fields[max_fields - 1 :]
    merged = "\n\n".join(f"**{field.name}**\n{field.value}" for field in overflow)
    if len(merged) > 1024:
        merged = merged[:1021] + "…"
    embed.clear_fields()
    for field in keep:
        embed.add_field(name=field.name, value=field.value, inline=field.inline)
    embed.add_field(name="More", value=merged, inline=False)
    return embed
