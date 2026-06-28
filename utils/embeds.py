import discord

from config import BOT_DISPLAY_NAME

EMBED_COLOR = discord.Color.from_rgb(139, 119, 90)  # warm fur brown
SUCCESS_COLOR = discord.Color.from_rgb(107, 142, 90)
ERROR_COLOR = discord.Color.from_rgb(160, 82, 72)


def player_text(text: str | None) -> str:
    """Lowercase player-facing copy; preserves empty/None."""
    if not text:
        return text or ""
    return text.lower()


def player_message(text: str | None) -> str:
    """Plain slash reply text (non-embed)."""
    return player_text(text)


def choice_label(label: str, *, max_len: int = 100) -> str:
    """Lowercase autocomplete / Choice display name."""
    return player_text(label)[:max_len]


def embed_footer(*extra: str) -> str:
    """Standard Howlbert footer; optional suffix segments."""
    base = f"{BOT_DISPLAY_NAME} · wolf rp"
    if not extra:
        return base
    return f"{base} · {' · '.join(player_text(x) for x in extra if x)}"


class PlayerEmbed(discord.Embed):
    """Discord embed that lowercases all player-visible text."""

    def __init__(self, *args, **kwargs):
        if "title" in kwargs and kwargs["title"]:
            kwargs["title"] = player_text(kwargs["title"])
        if "description" in kwargs and kwargs["description"]:
            kwargs["description"] = player_text(kwargs["description"])
        super().__init__(*args, **kwargs)

    def __setattr__(self, name: str, value) -> None:
        if name in ("title", "description") and isinstance(value, str):
            value = player_text(value)
        super().__setattr__(name, value)

    def add_field(self, *, name, value, inline: bool = True):
        return super().add_field(
            name=player_text(name),
            value=player_text(value),
            inline=inline,
        )

    def insert_field_at(self, index: int, *, name, value, inline: bool = True):
        return super().insert_field_at(
            index,
            name=player_text(name),
            value=player_text(value),
            inline=inline,
        )

    def set_footer(self, *, text=..., icon_url=...):
        if text is not ... and text is not None:
            text = player_text(text)
        if icon_url is ...:
            return super().set_footer(text=text)
        if not icon_url:
            return super().set_footer(text=text, icon_url=None)
        return super().set_footer(text=text, icon_url=icon_url)

    def set_author(self, *, name=..., url=..., icon_url=...):
        if name is not ... and name is not None:
            name = player_text(name)
        kwargs: dict[str, object] = {}
        if name is not ...:
            kwargs["name"] = name
        if url is not ...:
            kwargs["url"] = url
        if icon_url is not ...:
            kwargs["icon_url"] = icon_url
        return super().set_author(**kwargs)


def howlbert_embed(title: str, description: str = "", *, color=EMBED_COLOR) -> PlayerEmbed:
    embed = PlayerEmbed(title=title, description=description, color=color)
    embed.set_footer(text=embed_footer())
    return embed


def normalize_player_embed(embed: discord.Embed) -> PlayerEmbed:
    """Convert any embed to PlayerEmbed with lowercased visible text."""
    if isinstance(embed, PlayerEmbed):
        return embed
    normalized = PlayerEmbed(
        title=embed.title,
        description=embed.description or "",
        color=embed.color or EMBED_COLOR,
        url=embed.url,
    )
    if embed.author:
        normalized.set_author(
            name=embed.author.name,
            url=embed.author.url,
            icon_url=embed.author.icon_url,
        )
    for field in embed.fields:
        normalized.add_field(name=field.name, value=field.value, inline=field.inline)
    if embed.footer and embed.footer.text:
        normalized.set_footer(text=embed.footer.text, icon_url=embed.footer.icon_url)
    if embed.image:
        normalized.set_image(url=embed.image.url)
    if embed.thumbnail:
        normalized.set_thumbnail(url=embed.thumbnail.url)
    return normalized


def trim_embed_fields(embed: discord.Embed, max_fields: int = 25) -> discord.Embed:
    """Fold overflow fields into one block so Discord accepts the embed (max 25 fields)."""
    embed = normalize_player_embed(embed)
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
    embed.add_field(name="more", value=merged, inline=False)
    return embed
