import os
import re
import io
import time
import random
import sqlite3
import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
LINKS_PER_GEN = int(os.getenv("LINKS_PER_GEN", "3"))
MAX_PER_GEN = int(os.getenv("MAX_PER_GEN", "10000"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "0"))
LOW_STOCK = int(os.getenv("LOW_STOCK", "10"))  # mostra ⚠️ quando o estoque fica nesse número ou abaixo
# IDs extras com acesso admin, separados por vírgula
ADMIN_USER_IDS = {int(x) for x in os.getenv("ADMIN_USER_IDS", "").replace(" ", "").split(",") if x}
ADMIN_ROLE_IDS = {int(x) for x in os.getenv("ADMIN_ROLE_IDS", "").replace(" ", "").split(",") if x}
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.db"))

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# frase aleatória que aparece embaixo de cada /link1 (uma por linha em frases.txt)
FRASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frases.txt")
_frases_cache: tuple[float, list[str]] = (0.0, [])


def random_frase() -> str:
    # relê o arquivo quando ele muda, então dá pra editar as frases sem reiniciar o bot
    global _frases_cache
    try:
        mtime = os.path.getmtime(FRASES_PATH)
        if mtime != _frases_cache[0]:
            with open(FRASES_PATH, encoding="utf-8") as f:
                _frases_cache = (mtime, [line.strip() for line in f if line.strip()])
    except OSError:
        pass
    return random.choice(_frases_cache[1]) if _frases_cache[1] else "wupc é o melhor 👑"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("linkgen")


# ---------- banco de dados ----------

db = sqlite3.connect(DB_PATH)
db.execute(
    """CREATE TABLE IF NOT EXISTS links (
        url      TEXT PRIMARY KEY,
        used     INTEGER NOT NULL DEFAULT 0,
        used_by  TEXT,
        used_at  TEXT,
        added_at TEXT NOT NULL
    )"""
)
db.commit()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def extract_links(text: str) -> list[str]:
    seen, out = set(), []
    for m in URL_RE.findall(text):
        url = m.rstrip(".,;)]}")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def add_links(urls: list[str]) -> tuple[int, int]:
    added = 0
    for url in urls:
        cur = db.execute("INSERT OR IGNORE INTO links (url, added_at) VALUES (?, ?)", (url, now()))
        added += cur.rowcount
    db.commit()
    return added, len(urls) - added


def stock() -> tuple[int, int]:
    available = db.execute("SELECT COUNT(*) FROM links WHERE used = 0").fetchone()[0]
    used = db.execute("SELECT COUNT(*) FROM links WHERE used = 1").fetchone()[0]
    return available, used


def take_links(n: int, user_id: int) -> list[str]:
    rows = db.execute("SELECT url FROM links WHERE used = 0 ORDER BY RANDOM() LIMIT ?", (n,)).fetchall()
    urls = [r[0] for r in rows]
    db.executemany(
        "UPDATE links SET used = 1, used_by = ?, used_at = ? WHERE url = ?",
        [(str(user_id), now(), u) for u in urls],
    )
    db.commit()
    return urls


# ---------- bot ----------

class LinkGen(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        app = await self.application_info()
        if app.team:
            owner_ids.update(m.id for m in app.team.members)
        else:
            owner_ids.add(app.owner.id)
        log.info("Donos (admin automático): %s", owner_ids)

        # registra os comandos globais (substitui os do bot antigo)
        synced = await self.tree.sync()
        log.info("Comandos sincronizados: %s", ", ".join(c.name for c in synced))

    async def on_ready(self):
        # remove comandos antigos registrados só no servidor, para não aparecerem duplicados
        for guild in self.guilds:
            try:
                await self.tree.sync(guild=guild)
            except discord.HTTPException as e:
                log.warning("Falha ao limpar comandos de %s: %s", guild.name, e)
        log.info("Online como %s em %d servidor(es)", self.user, len(self.guilds))


client = LinkGen()
last_use: dict[int, float] = {}
owner_ids: set[int] = set()  # dono(s) da aplicação no Developer Portal, sempre admin


def is_admin(inter: discord.Interaction) -> bool:
    if inter.user.id in ADMIN_USER_IDS or inter.user.id in owner_ids:
        return True
    roles = getattr(inter.user, "roles", [])
    if any(r.id in ADMIN_ROLE_IDS for r in roles):
        return True
    perms = getattr(inter.user, "guild_permissions", None)
    return bool(perms and (perms.administrator or perms.manage_guild))


async def deny(inter: discord.Interaction):
    log.info("Acesso negado: %s (id %s)", inter.user, inter.user.id)
    await inter.response.send_message("❌ Só administradores podem usar esse comando.", ephemeral=True)


def stock_text() -> str:
    available, used = stock()
    return f"📦 **Disponíveis:** {available}\n🔁 **Usados:** {used}\n📊 **Total:** {available + used}"


@client.tree.command(name="link1", description="Gera links aleatórios da lista")
@app_commands.describe(quantidade=f"Quantos links gerar (padrão {LINKS_PER_GEN})")
async def link1(inter: discord.Interaction, quantidade: app_commands.Range[int, 1, MAX_PER_GEN] = LINKS_PER_GEN):
    if COOLDOWN_SECONDS and not is_admin(inter):
        wait = COOLDOWN_SECONDS - (time.monotonic() - last_use.get(inter.user.id, 0))
        if wait > 0:
            await inter.response.send_message(f"⏳ Espera {int(wait) + 1}s pra gerar de novo.", ephemeral=True)
            return

    urls = take_links(quantidade, inter.user.id)
    if not urls:
        await inter.response.send_message("😕 Acabaram os links. Avisa um administrador.", ephemeral=True)
        return

    last_use[inter.user.id] = time.monotonic()
    header = "LINK GERADO! 🔥"
    if len(urls) < quantidade:
        header += f"\n⚠️ Só tinha **{len(urls)}** no estoque."
    remaining = stock()[0]
    footer = f"📦 Restam **{remaining}** links no estoque" + (" ⚠️" if remaining <= LOW_STOCK else "")
    footer += f"\n\n*{random_frase()}*"
    text = header + "\n\n" + "\n".join(urls) + "\n\n" + footer
    if len(text) <= 2000:
        await inter.response.send_message(text, suppress_embeds=True)
    else:
        # mensagem do Discord tem limite de 2000 caracteres: muitos links vão em .txt
        file = discord.File(io.BytesIO("\n".join(urls).encode()), filename=f"links_{len(urls)}.txt")
        await inter.response.send_message(f"{header}\n📎 **{len(urls)}** links no arquivo:\n\n{footer}", file=file)


@client.tree.command(name="stock", description="Mostra quantos links tem disponíveis")
async def stock_cmd(inter: discord.Interaction):
    await inter.response.send_message(stock_text())


@client.tree.command(name="addlink", description="Adiciona um ou vários links na lista (só admin)")
@app_commands.describe(links="Um ou vários links, separados por espaço")
async def addlink(inter: discord.Interaction, links: str):
    if not is_admin(inter):
        return await deny(inter)
    urls = extract_links(links)
    if not urls:
        await inter.response.send_message("❌ Não achei nenhum link válido (tem que começar com http:// ou https://).", ephemeral=True)
        return
    added, dup = add_links(urls)
    await inter.response.send_message(f"✅ Adicionados: **{added}** · Repetidos: **{dup}**\n\n{stock_text()}", ephemeral=True)


@client.tree.command(name="uploadlinks", description="Envia um arquivo .txt com links, um por linha (só admin)")
@app_commands.describe(arquivo="Arquivo .txt com os links")
async def uploadlinks(inter: discord.Interaction, arquivo: discord.Attachment):
    if not is_admin(inter):
        return await deny(inter)
    if arquivo.size > 5 * 1024 * 1024:
        await inter.response.send_message("❌ Arquivo muito grande (máx. 5 MB).", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    data = await arquivo.read()
    urls = extract_links(data.decode("utf-8", errors="ignore"))
    if not urls:
        await inter.followup.send("❌ O arquivo não tem nenhum link válido.", ephemeral=True)
        return
    added, dup = add_links(urls)
    await inter.followup.send(
        f"✅ Arquivo processado: **{len(urls)}** links\nAdicionados: **{added}** · Repetidos: **{dup}**\n\n{stock_text()}",
        ephemeral=True,
    )


@client.tree.command(name="removelink", description="Remove um link da lista (só admin)")
@app_commands.describe(link="Link para remover")
async def removelink(inter: discord.Interaction, link: str):
    if not is_admin(inter):
        return await deny(inter)
    cur = db.execute("DELETE FROM links WHERE url = ?", (link.strip(),))
    db.commit()
    msg = "🗑️ Link removido." if cur.rowcount else "❌ Esse link não está na lista."
    await inter.response.send_message(f"{msg}\n\n{stock_text()}", ephemeral=True)


@client.tree.command(name="removelinks", description="Remove em massa os links de um arquivo .txt, um por linha (só admin)")
@app_commands.describe(arquivo="Arquivo .txt com os links para remover")
async def removelinks(inter: discord.Interaction, arquivo: discord.Attachment):
    if not is_admin(inter):
        return await deny(inter)
    if arquivo.size > 5 * 1024 * 1024:
        await inter.response.send_message("❌ Arquivo muito grande (máx. 5 MB).", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    data = await arquivo.read()
    urls = extract_links(data.decode("utf-8", errors="ignore"))
    if not urls:
        await inter.followup.send("❌ O arquivo não tem nenhum link válido.", ephemeral=True)
        return
    removed = 0
    for url in urls:
        removed += db.execute("DELETE FROM links WHERE url = ?", (url,)).rowcount
    db.commit()
    await inter.followup.send(
        f"🗑️ Arquivo processado: **{len(urls)}** links\nRemovidos: **{removed}** · Não estavam na lista: **{len(urls) - removed}**\n\n{stock_text()}",
        ephemeral=True,
    )


@client.tree.command(name="reloadlinks", description="Devolve todos os links usados para o estoque (só admin)")
async def reloadlinks(inter: discord.Interaction):
    if not is_admin(inter):
        return await deny(inter)
    cur = db.execute("UPDATE links SET used = 0, used_by = NULL, used_at = NULL WHERE used = 1")
    db.commit()
    await inter.response.send_message(f"♻️ **{cur.rowcount}** links voltaram pro estoque.\n\n{stock_text()}", ephemeral=True)


@client.tree.command(name="exportlinks", description="Baixa todos os links em um .txt (só admin)")
async def exportlinks(inter: discord.Interaction):
    if not is_admin(inter):
        return await deny(inter)
    rows = db.execute("SELECT url, used FROM links ORDER BY used, added_at").fetchall()
    body = "\n".join(f"{url}\t{'usado' if used else 'disponível'}" for url, used in rows) or "(vazio)"
    file = discord.File(io.BytesIO(body.encode()), filename="links.txt")
    await inter.response.send_message(stock_text(), file=file, ephemeral=True)


@client.tree.command(name="clearlinks", description="Apaga TODOS os links da lista (só admin)")
@app_commands.describe(confirmar="Digite APAGAR para confirmar")
async def clearlinks(inter: discord.Interaction, confirmar: str):
    if not is_admin(inter):
        return await deny(inter)
    if confirmar != "APAGAR":
        await inter.response.send_message("Cancelado. Digite exatamente `APAGAR` para confirmar.", ephemeral=True)
        return
    cur = db.execute("DELETE FROM links")
    db.commit()
    await inter.response.send_message(f"🧹 {cur.rowcount} links apagados.", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN não configurado. Rode: /opt/linkgen/set-token.sh")
    client.run(TOKEN, log_handler=None)
