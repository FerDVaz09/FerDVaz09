"""
Abacus GPT - Bot de Discord con IA para soporte técnico de TradeStation
Autor: Ingeniero de Software Senior
Fecha: 2025-11-24

Este bot escucha reacciones específicas (🤖) en mensajes de Discord,
crea hilos privados para interacciones 1:1 con OpenAI, y auto-elimina
los hilos después de 24 horas.
"""

import discord
from discord.ext import tasks, commands
import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import asyncio
from typing import Dict, Any, Optional, Tuple

# OpenAI API v1 (nuevo cliente)
from openai import OpenAI
import openai  # Para tipos de excepciones si se requieren

# ==================== CONFIGURACIÓN ====================

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener credenciales
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_raw_message_id = (os.getenv("MESSAGE_ID") or "").strip()
try:
    TRIGGER_MESSAGE_ID = int(_raw_message_id)
except ValueError:
    TRIGGER_MESSAGE_ID = 0

# Instanciar cliente OpenAI (la librería toma API Key del entorno si existe)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Archivo para persistencia de hilos activos
THREADS_FILE = "active_threads.json"

try:
    from knowledge_base import build_context
except ImportError:
    build_context = None  # type: ignore

# System Prompt para la IA
SYSTEM_PROMPT = """Eres un experto en inversiones y TradeStation, especializado en el lenguaje EasyLanguage. 
Tu objetivo es proporcionar soporte técnico y educativo de alta calidad.

IMPORTANTE: No das consejos financieros de compra/venta de acciones, criptomonedas o cualquier instrumento financiero. 
Solo ofreces soporte técnico sobre el uso de la plataforma TradeStation y ayuda para programar en EasyLanguage.

Debes ser profesional, claro y educativo en tus respuestas."""

# ==================== INTENTS Y BOT ====================

# Configurar intents necesarios para el bot
intents = discord.Intents.default()
intents.message_content = True  # Para leer contenido de mensajes
intents.reactions = True  # Para detectar reacciones
intents.guilds = True  # Para acceder a servidores
intents.members = True  # Para mencionar usuarios

# Crear instancia del bot
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== GESTIÓN DE HILOS ====================

def load_threads() -> Dict[str, Dict[str, Any]]:
    """
    Carga los hilos activos desde el archivo JSON.
    Si el archivo no existe, retorna un diccionario vacío.
    """
    try:
        if os.path.exists(THREADS_FILE):
            with open(THREADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️ Error al cargar hilos: {e}")
        return {}


def save_threads(threads_data):
    """
    Guarda los hilos activos en el archivo JSON.
    """
    try:
        with open(THREADS_FILE, "w", encoding="utf-8") as f:
            json.dump(threads_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error al guardar hilos: {e}")


def add_thread(thread_id, user_id, created_at):
    """
    Añade un nuevo hilo al registro de hilos activos.
    """
    threads = load_threads()
    threads[str(thread_id)] = {
        "user_id": user_id,
        "created_at": created_at.isoformat()
    }
    save_threads(threads)


def remove_thread(thread_id):
    """
    Elimina un hilo del registro de hilos activos.
    """
    threads = load_threads()
    if str(thread_id) in threads:
        del threads[str(thread_id)]
        save_threads(threads)


def get_recent_thread_entry(
    user_id: int,
    within_hours: int = 24,
    threads: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Optional[Tuple[int, datetime]]:
    """Return the most recent thread id for a user within the given timeframe."""
    if threads is None:
        threads = load_threads()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    latest: Optional[Tuple[int, datetime]] = None

    for thread_id_str, data in threads.items():
        if str(data.get("user_id")) != str(user_id):
            continue

        created_at_iso = data.get("created_at")
        if not created_at_iso:
            continue

        try:
            created_at = datetime.fromisoformat(created_at_iso)
        except Exception:
            continue

        if created_at < cutoff:
            continue

        thread_id = int(thread_id_str)
        if latest is None or created_at > latest[1]:
            latest = (thread_id, created_at)

    return latest


async def fetch_thread_by_id(guild: Optional[discord.Guild], thread_id: int) -> Optional[discord.Thread]:
    """Retrieve a thread channel safely, returning None if inaccessible."""
    if guild is None:
        return None

    thread = guild.get_thread(thread_id)
    if isinstance(thread, discord.Thread):
        return thread

    try:
        channel = await guild.fetch_channel(thread_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None

    return channel if isinstance(channel, discord.Thread) else None

# ==================== EVENTOS DEL BOT ====================

@bot.event
async def on_ready():
    """
    Evento que se ejecuta cuando el bot está listo y conectado.
    """
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📊 Conectado a {len(bot.guilds)} servidor(es)")
    print(f"🤖 Emoji trigger: 🤖")
    print(f"📝 ID del mensaje trigger: {TRIGGER_MESSAGE_ID}")
    
    # Iniciar tarea de limpieza de hilos
    if not cleanup_old_threads.is_running():
        cleanup_old_threads.start()
        print("🧹 Tarea de limpieza de hilos iniciada")


@bot.event
async def on_reaction_add(reaction, user):
    """
    Evento que se ejecuta cuando alguien añade una reacción a un mensaje.
    
    Lógica:
    1. Verifica que no sea el propio bot quien reaccionó
    2. Verifica que el emoji sea 🤖
    3. Verifica que sea el mensaje correcto (por ID)
    4. Crea un hilo privado con el usuario
    """
    # Logs de depuración iniciales
    try:
        print(f"[DEBUG on_reaction_add] emoji={reaction.emoji} msg_id={reaction.message.id} user={user.id} bot?={user.bot}")
    except Exception:
        pass

    # Ignorar reacciones del propio bot
    if user.bot:
        return

    # Verificar que sea el emoji correcto
    if str(reaction.emoji) != "🤖":
        print("[DEBUG on_reaction_add] Emoji distinto, ignorando")
        return

    # Verificar que sea el mensaje correcto
    if reaction.message.id != TRIGGER_MESSAGE_ID:
        print(f"[DEBUG on_reaction_add] MESSAGE_ID no coincide ({reaction.message.id} != {TRIGGER_MESSAGE_ID})")
        return
    
    threads = load_threads()
    recent_entry = get_recent_thread_entry(user.id, threads=threads)

    if recent_entry:
        existing_thread_id, _ = recent_entry
        existing_thread = await fetch_thread_by_id(reaction.message.guild, existing_thread_id)

        try:
            await reaction.message.remove_reaction("🤖", user)
        except (discord.Forbidden, discord.HTTPException):
            pass

        if existing_thread is None:
            remove_thread(existing_thread_id)
        else:
            try:
                await existing_thread.add_user(user)
            except (discord.Forbidden, discord.HTTPException):
                pass

            try:
                await existing_thread.send(
                    f"{user.mention} ya tienes un ticket abierto en las últimas 24 horas. Continuemos aquí 🧠"
                )
            except (discord.Forbidden, discord.HTTPException):
                pass

            thread_link = f"https://discord.com/channels/{existing_thread.guild.id}/{existing_thread.id}"
            try:
                await user.send(
                    "Ya tienes un ticket activo en Abacus GPT. Puedes retomarlo aquí: "
                    f"{thread_link}"
                )
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

    try:
        channel = reaction.message.channel
        thread = None
        try:
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
        except TypeError:
            print("[WARN] create_thread no acepta 'type'; creando hilo público como fallback")
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440
            )
        except discord.Forbidden:
            print("⚠️ Permisos insuficientes para crear hilo privado; intento hilo público")
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440
            )

        await thread.add_user(user)
        add_thread(thread.id, user.id, datetime.now(timezone.utc))

        welcome_message = f"""👋 ¡Hola {user.mention}!

Soy **Abacus GPT**, tu asistente personal para soporte técnico sobre **TradeStation** y **EasyLanguage**.

🔹 Puedes hacerme cualquier pregunta sobre:
   • Uso de la plataforma TradeStation
   • Programación en EasyLanguage
   • Configuración de indicadores y estrategias
   • Resolución de errores técnicos

⚠️ **IMPORTANTE**: No proporciono consejos financieros de compra/venta. Solo soporte técnico y educativo.

🕒 Este hilo se auto-eliminará en **24 horas**.

¿En qué puedo ayudarte hoy?"""

        await thread.send(welcome_message)

        print(f"✅ Hilo creado para {user.name} (ID: {thread.id})")

    except discord.Forbidden:
        print(f"⚠️ No tengo permisos para crear hilos en {reaction.message.channel.name}")
    except Exception as e:
        print(f"❌ Error al crear hilo: {e}")


# ==============================================================
# EVENTO ALTERNATIVO: RAW REACTION ADD
# Este evento se dispara incluso si el mensaje no está en caché.
# Útil cuando el bot se inicia después de que el mensaje trigger ya existe.
# ==============================================================
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Captura reacciones incluso cuando el mensaje no está cacheado.

    Razones para usarlo:
    - El bot se inició después de que el mensaje existiera
    - El mensaje no está en cache local
    - Se quiere mayor robustez en la detección de reacciones
    """
    try:
        print(f"[DEBUG raw] guild={payload.guild_id} channel={payload.channel_id} message={payload.message_id} user={payload.user_id} emoji={payload.emoji}")
        # Ignorar reacciones del propio bot
        if payload.user_id == bot.user.id:
            return

        # Verificar emoji
        if str(payload.emoji) != "🤖":
            print("[DEBUG raw] Emoji distinto, ignorando")
            return

        # Verificar mensaje correcto
        if payload.message_id != TRIGGER_MESSAGE_ID:
            print(f"[DEBUG raw] MESSAGE_ID no coincide ({payload.message_id} != {TRIGGER_MESSAGE_ID})")
            return

        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            # Intentar obtener el guild de otra forma (poco común)
            guild = await bot.fetch_guild(payload.guild_id)

        # Obtener canal
        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            channel = await bot.fetch_channel(payload.channel_id)

        # Traer mensaje (ya que no estaba cacheado)
        message = await channel.fetch_message(payload.message_id)

        # Obtener usuario
        user = guild.get_member(payload.user_id)
        if user is None:
            user = await guild.fetch_member(payload.user_id)

        threads = load_threads()
        recent_entry = get_recent_thread_entry(user.id, threads=threads)

        if recent_entry:
            existing_thread_id, _ = recent_entry
            existing_thread = await fetch_thread_by_id(guild, existing_thread_id)

            try:
                await message.remove_reaction("🤖", user)
            except (discord.Forbidden, discord.HTTPException):
                pass

            if existing_thread is None:
                remove_thread(existing_thread_id)
            else:
                try:
                    await existing_thread.add_user(user)
                except (discord.Forbidden, discord.HTTPException):
                    pass

                try:
                    await existing_thread.send(
                        f"{user.mention} ya tienes un ticket abierto en las últimas 24 horas. Continuemos aquí 🧠"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

                thread_link = f"https://discord.com/channels/{existing_thread.guild.id}/{existing_thread.id}"
                try:
                    await user.send(
                        "Ya tienes un ticket activo en Abacus GPT. Puedes retomarlo aquí: "
                        f"{thread_link}"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
                return

        # Crear hilo privado
        channel = message.channel
        thread = None
        try:
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
        except TypeError:
            print("[WARN RAW] create_thread no acepta 'type'; creando hilo público fallback")
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440
            )
        except discord.Forbidden:
            print("⚠️ (RAW) Permisos insuficientes para hilo privado; intento público")
            thread = await channel.create_thread(
                name=f"Soporte para {user.name}",
                auto_archive_duration=1440
            )

        await thread.add_user(user)
        add_thread(thread.id, user.id, datetime.now(timezone.utc))

        welcome_message = f"""👋 ¡Hola {user.mention}!

Soy **Abacus GPT**, tu asistente personal para soporte técnico sobre **TradeStation** y **EasyLanguage**.

Has activado este hilo vía reacción 🤖 en el mensaje de soporte.

⚠️ No doy consejos de inversión (compra/venta). Solo ayuda técnica y educativa.

🕒 Este hilo se auto-eliminará en 24h.

¿En qué puedo ayudarte hoy?"""
        await thread.send(welcome_message)
        print(f"✅ (RAW) Hilo creado para {user.name} (ID: {thread.id})")

    except discord.Forbidden:
        print("⚠️ Permisos insuficientes para crear hilo en canal (RAW) - verificar 'Create Private Threads' y 'Manage Threads'")
    except Exception as e:
        print(f"❌ Error en on_raw_reaction_add: {e}")

# ==============================================================
# Comando auxiliar: crear hilo manualmente para pruebas
# ==============================================================
@bot.command(name="makethread")
@commands.has_permissions(manage_threads=True)
async def make_thread(ctx):
    """Crea un hilo privado manual para pruebas de permisos."""
    try:
        thread = await ctx.message.channel.create_thread(
            name=f"TestThread-{ctx.author.name}",
            auto_archive_duration=1440,
            type=discord.ChannelType.private_thread
        )
        await thread.add_user(ctx.author)
        add_thread(thread.id, ctx.author.id, datetime.now(timezone.utc))
        await thread.send("Hilo de prueba creado correctamente. Escribe un mensaje para probar la integración con IA (si está en lista de hilos).")
        await ctx.reply(f"✅ Hilo de prueba creado: {thread.id}")
        print(f"✅ (COMANDO) Hilo de prueba creado {thread.id}")
    except discord.Forbidden:
        await ctx.reply("❌ No tengo permisos para crear hilos privados en este canal.")
    except Exception as e:
        await ctx.reply(f"❌ Error creando hilo: {e}")
        print(f"❌ Error comando makethread: {e}")


@bot.event
async def on_message(message):
    """
    Evento que se ejecuta cuando se envía un mensaje.
    
    Lógica:
    1. Verifica que el mensaje sea en un hilo privado
    2. Verifica que el autor no sea el bot
    3. Verifica que el hilo esté registrado en nuestro sistema
    4. Envía el mensaje a OpenAI y responde
    """
    # Ignorar mensajes del propio bot
    if message.author.bot:
        return
    
    # Verificar que sea un hilo privado
    if not isinstance(message.channel, discord.Thread):
        return
    
    if message.channel.type != discord.ChannelType.private_thread:
        return
    
    # Verificar que el hilo esté en nuestro sistema
    threads = load_threads()
    if str(message.channel.id) not in threads:
        return
    
    try:
        # Mostrar indicador de "escribiendo..."
        async with message.channel.typing():
            # Enviar mensaje a OpenAI
            response = await get_ai_response(message.content)
            
            # Dividir respuesta si es muy larga (límite de Discord: 2000 caracteres)
            if len(response) > 2000:
                # Dividir en chunks de 2000 caracteres
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)
        
        print(f"💬 Respuesta enviada en hilo {message.channel.id}")
        
    except openai.RateLimitError:
        await message.channel.send("⚠️ **Límite alcanzado**: Se excedió el número de solicitudes permitidas. Intenta nuevamente en un minuto.")
        print("⚠️ RateLimitError OpenAI")
    except openai.AuthenticationError:
        await message.channel.send("❌ **Error autenticación**: La API Key es inválida o no tiene permisos. Revisa configuración.")
        print("❌ AuthenticationError OpenAI")
    except openai.APIError as e:
        await message.channel.send("⚠️ **Error de servicio**: OpenAI tuvo un problema interno. Intenta más tarde.")
        print(f"❌ APIError OpenAI: {e}")
    except Exception as e:
        await message.channel.send("⚠️ **Error inesperado** procesando tu solicitud. Intenta nuevamente.")
        print(f"❌ Excepción genérica OpenAI: {e}")


# ==================== INTEGRACIÓN CON OPENAI ====================

async def get_ai_response(user_message: str) -> str:
    """Genera respuesta usando OpenAI Chat Completions API v1.

    Usa el cliente oficial nuevo. Maneja chunking largo en capa superior.
    """
    if client is None:
        return "⚠️ Configuración incompleta de OpenAI (falta API Key)."

    context_blob = ""
    if build_context is not None:
        try:
            context_blob = build_context(user_message)
        except Exception as context_error:  # pragma: no cover - resiliencia
            context_blob = ""
            print(f"[WARN] No se pudo generar contexto desde knowledge_base: {context_error}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context_blob:
        messages.append({"role": "system", "content": context_blob})
    messages.append({"role": "user", "content": user_message})

    try:
        # Ejecutar llamado bloqueante en thread aparte
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",  # Modelo eficiente; cambiar a gpt-4o si se desea
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        content = response.choices[0].message.content if response.choices else "(Respuesta vacía)"
        return content.strip()
    except Exception as e:
        print(f"❌ Error en get_ai_response: {e}")
        raise


# ==================== TAREA DE LIMPIEZA ====================

@tasks.loop(minutes=1)
async def cleanup_old_threads():
    """
    Tarea en bucle que se ejecuta cada minuto.
    
    Lógica:
    1. Carga todos los hilos activos
    2. Verifica si algún hilo tiene más de 24 horas
    3. Elimina los hilos antiguos
    """
    threads = load_threads()
    now = datetime.now(timezone.utc)
    threads_to_remove = []
    
    for thread_id_str, thread_data in threads.items():
        try:
            # Parsear fecha de creación
            created_at = datetime.fromisoformat(thread_data["created_at"])
            
            # Calcular edad del hilo
            age = now - created_at
            
            # Si tiene más de 24 horas, marcarlo para eliminación
            if age > timedelta(hours=24):
                thread_id = int(thread_id_str)
                
                # Intentar obtener el hilo
                thread = bot.get_channel(thread_id)
                
                if thread is None:
                    # Si no se encuentra, intentar buscarlo
                    try:
                        thread = await bot.fetch_channel(thread_id)
                    except discord.NotFound:
                        # El hilo ya no existe, remover del registro
                        threads_to_remove.append(thread_id_str)
                        print(f"🗑️ Hilo {thread_id} ya no existe, removido del registro")
                        continue
                
                if thread:
                    try:
                        # Enviar mensaje de despedida
                        await thread.send("⏰ Este hilo ha alcanzado las 24 horas y será eliminado. ¡Gracias por usar Abacus GPT!")
                        await asyncio.sleep(2)  # Esperar 2 segundos
                        
                        # Eliminar el hilo
                        await thread.delete()
                        threads_to_remove.append(thread_id_str)
                        print(f"🗑️ Hilo {thread_id} eliminado (más de 24 horas)")
                    
                    except discord.Forbidden:
                        print(f"⚠️ No tengo permisos para eliminar hilo {thread_id}")
                    except discord.NotFound:
                        threads_to_remove.append(thread_id_str)
                        print(f"🗑️ Hilo {thread_id} no encontrado, removido del registro")
        
        except Exception as e:
            print(f"❌ Error al procesar hilo {thread_id_str}: {e}")
    
    # Remover hilos del registro
    for thread_id_str in threads_to_remove:
        remove_thread(int(thread_id_str))


@cleanup_old_threads.before_loop
async def before_cleanup():
    """
    Espera a que el bot esté listo antes de iniciar la tarea de limpieza.
    """
    await bot.wait_until_ready()


# ==================== COMANDOS DE ADMINISTRACIÓN ====================

@bot.command(name="ping")
@commands.has_permissions(administrator=True)
async def ping(ctx):
    """
    Comando de prueba para verificar que el bot está funcionando.
    Solo para administradores.
    """
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latencia: {latency}ms")


@bot.command(name="threads")
@commands.has_permissions(administrator=True)
async def list_threads(ctx):
    """
    Lista todos los hilos activos.
    Solo para administradores.
    """
    threads = load_threads()
    
    if not threads:
        await ctx.send("📋 No hay hilos activos en este momento.")
        return
    
    message = "📋 **Hilos Activos:**\n\n"
    for thread_id, data in threads.items():
        created_at = datetime.fromisoformat(data["created_at"])
        age = datetime.utcnow() - created_at
        hours = int(age.total_seconds() / 3600)
        minutes = int((age.total_seconds() % 3600) / 60)
        
        message += f"• Hilo ID: `{thread_id}` - Usuario: <@{data['user_id']}> - Edad: {hours}h {minutes}m\n"
    
    await ctx.send(message)


# ==================== INICIAR BOT ====================

if __name__ == "__main__":
    # Verificar que las variables de entorno estén configuradas
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN no está configurado en .env")
        exit(1)
    
    if not OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY no está configurado en .env")
        exit(1)
    
    if TRIGGER_MESSAGE_ID == 0:
        if _raw_message_id:
            print(f"⚠️ ADVERTENCIA: MESSAGE_ID inválido ('{_raw_message_id}'). Revisa el valor en .env")
        else:
            print("⚠️ ADVERTENCIA: MESSAGE_ID no está configurado en .env")
        print("   El bot no reaccionará a ningún mensaje hasta que configures MESSAGE_ID")
    
    # Iniciar el bot
    try:
        print("🚀 Iniciando Abacus GPT...")
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ ERROR: Token de Discord inválido")
    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")