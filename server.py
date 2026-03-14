import asyncio
import aiosqlite

db = None
active_usernames = set()

async def init_db():
    global db
    db = await aiosqlite.connect('messenger.db')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await db.commit()
    print("💾 База данных подключена (messenger.db)")

async def save_message(username, content):
    await db.execute(
        'INSERT INTO messages (username, content) VALUES (?, ?)',
        (username, content)
    )
    await db.commit()

async def get_last_messages(limit=200):
    async with db.execute(
        'SELECT username, content, timestamp FROM messages ORDER BY id DESC LIMIT ?',
        (limit,)
    ) as cursor:
        rows = await cursor.fetchall()
    return reversed(rows)

async def is_username_taken(username):
    return username in active_usernames

async def register_username(username):
    active_usernames.add(username)

async def unregister_username(username):
    active_usernames.discard(username)

clients = {}

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"🔌 Новое подключение от {addr}")
    
    writer.write("🔐 Введите ваш логин: ".encode())
    await writer.drain()
    
    login_data = await reader.readline()
    username = login_data.decode('utf-8').strip()
    
    if not username or len(username) > 20:
        writer.write("❌ Неверный логин. Отключено.\n".encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return
    
    if await is_username_taken(username):
        writer.write(f"❌ Ник '{username}' уже занят. Отключено.\n".encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return
    
    await register_username(username)
    clients[writer] = {"username": username, "authenticated": True}
    print(f"✅ Авторизован: {username} ({addr})")
    
    # История сообщений (200)
    history = await get_last_messages(200)
    writer.write("\n📜 История чата (последние 200):\n".encode())  # ✅ ИСПРАВЛЕНО
    for user, content, ts in history:
        writer.write(f"[{ts}] [{user}] {content}\n".encode())
    writer.write(("-" * 40 + "\n").encode())
    await writer.drain()
    
    writer.write(f"🎉 Добро пожаловать, {username}!\n".encode())
    await writer.drain()
    
    await broadcast(f"🟢 {username} присоединился к чату", writer)
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            if message:
                print(f"💬 [{username}]: {message}")
                await save_message(username, message)
                await broadcast(f"[{username}] {message}", None)
                
    except Exception as e:
        print(f"❌ Ошибка с {username}: {e}")
    finally:
        if writer in clients:
            name = clients[writer]["username"]
            del clients[writer]
            await unregister_username(name)
            await broadcast(f"🔴 {name} покинул чат", None)
            print(f"🔌 Отключился: {name}")
        writer.close()
        await writer.wait_closed()

async def broadcast(message, exclude_writer):
    for client, info in clients.items():
        if exclude_writer is None or client != exclude_writer:
            if info["authenticated"]:
                try:
                    client.write(f"{message}\n".encode())
                    await client.drain()
                except:
                    pass

async def main():
    await init_db()
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    print("🚀 Сервер мессенджера запущен на порту 8888")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")
