<div align="center">

# 🔗 LINKGEN

### Gerador de links para Discord — rápido, simples e direto ao ponto

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="discord.py">
  <img src="https://img.shields.io/badge/SQLite-banco-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Online-24%2F7-2ea44f?style=for-the-badge" alt="Online 24/7">
</p>

<p>
  <b>Feito por <a href="https://github.com/wupckoding">wupc</a> 👑</b>
</p>

</div>

---

## ✨ O que ele faz

O **LINKGEN** guarda um estoque de links e entrega links aleatórios pra quem usar `/link1` no servidor.
Cada link entregue **sai do estoque**, então ninguém recebe repetido, e você acompanha tudo em tempo real.

- 🎲 **Links aleatórios**: escolha quantos quer, de 1 até 10.000 por vez
- 📦 **Contador de estoque**: toda geração mostra quantos links ainda restam
- ⚠️ **Aviso de estoque baixo**: avisa quando está na hora de repor
- 📤 **Upload fácil**: manda um `.txt` com um link por linha e pronto
- 🗑️ **Remoção em massa**: manda um `.txt` com os links que quer tirar do estoque
- 🧹 **Sem duplicados**: links repetidos são ignorados automaticamente
- 📎 **Muitos links? Vira arquivo**: se não couber numa mensagem, o bot manda um `.txt`
- 💬 **Mais de 400 frases motivacionais** aleatórias embaixo de cada geração
- 🔒 **Comandos de admin protegidos**
- 🔁 **24/7**: reinicia sozinho se cair ou se o servidor reiniciar

---

## 🖼️ Como fica no Discord

```
LINK GERADO! 🔥

https://exemplo-1.com/
https://exemplo-2.com/
https://exemplo-3.com/

📦 Restam 47 links no estoque

wupc mandou você não desistir 💪
```

---

## 🕹️ Comandos

### Para todo mundo

| Comando | O que faz |
|---|---|
| `/link1` | Gera 3 links aleatórios |
| `/link1 quantidade:50` | Gera a quantidade que você escolher |
| `/stock` | Mostra quantos links estão disponíveis, usados e o total |

### Só para admins

| Comando | O que faz |
|---|---|
| `/uploadlinks arquivo:` | Envia um `.txt` com vários links (um por linha) |
| `/addlink links:` | Adiciona um ou vários links, separados por espaço |
| `/removelink link:` | Remove um link do estoque |
| `/removelinks arquivo:` | Remove em massa: envia um `.txt` com os links que quer tirar (um por linha) |
| `/reloadlinks` | Devolve todos os links usados para o estoque |
| `/exportlinks` | Baixa todos os links em `.txt`, com o status de cada um |
| `/clearlinks confirmar:APAGAR` | Apaga **todos** os links |

> 🔑 **Quem é admin?** O dono do bot no Discord Developer Portal, quem tem permissão de
> *Administrador* ou *Gerenciar Servidor*, e quem estiver em `ADMIN_USER_IDS` / `ADMIN_ROLE_IDS`.

---

## 🚀 Instalação (VPS Ubuntu)

```bash
# 1. Baixar o projeto
git clone https://github.com/wupckoding/bot-linkgen-discord.git /opt/linkgen
cd /opt/linkgen

# 2. Instalar dependências
apt install -y python3-venv
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
chmod +x set-token.sh

# 4. Ligar como serviço (roda 24/7)
cp linkgen.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable linkgen

# 5. Colocar o token (pede sem mostrar na tela e já liga o bot)
./set-token.sh
```

### 🔗 Convidar o bot

No [Developer Portal](https://discord.com/developers/applications), vá em **OAuth2 → URL Generator**, marque
`bot` + `applications.commands` e as permissões **Send Messages** e **Attach Files**.

---

## ⚙️ Configuração (`.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `DISCORD_TOKEN` | — | Token do bot (**obrigatório**) |
| `LINKS_PER_GEN` | `3` | Quantos links o `/link1` gera sem número |
| `MAX_PER_GEN` | `10000` | Máximo de links por geração |
| `COOLDOWN_SECONDS` | `0` | Espera entre usos por pessoa (admins ignoram) |
| `LOW_STOCK` | `10` | Abaixo disso aparece o ⚠️ de estoque baixo |
| `ADMIN_USER_IDS` | — | IDs de usuários admin, separados por vírgula |
| `ADMIN_ROLE_IDS` | — | IDs de cargos admin, separados por vírgula |

Depois de mudar o `.env`: `systemctl restart linkgen`

---

## 💬 Frases motivacionais

As frases ficam em [`frases.txt`](frases.txt), **uma por linha**.
Pode adicionar, remover ou editar à vontade: o bot pega as mudanças **sem precisar reiniciar**.

---

## 🛠️ Comandos úteis na VPS

```bash
systemctl status linkgen        # ver se está rodando
journalctl -u linkgen -f        # ver os logs ao vivo
systemctl restart linkgen       # reiniciar
cd /opt/linkgen && git pull && systemctl restart linkgen   # atualizar
```

---

## 📁 Estrutura

```
bot-linkgen-discord/
├── bot.py             # o bot
├── frases.txt         # 400+ frases aleatórias
├── requirements.txt   # dependências
├── linkgen.service    # serviço systemd (24/7)
├── set-token.sh       # salva o token com segurança
└── .env.example       # modelo de configuração
```

> 🔐 O `.env` (token) e o `links.db` (estoque de links) **nunca** vão pro GitHub, e estão no `.gitignore`.

---

<div align="center">

## 👑 Créditos

Criado e mantido por **[wupc](https://github.com/wupckoding)**

*wupc mandou você não desistir* 💪

⭐ Se curtiu, deixa uma estrela no repositório!

</div>
