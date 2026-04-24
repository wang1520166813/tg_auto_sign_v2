import os
import sys
import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

# 兼容性设置：防止 Windows 下事件循环策略问题
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, 
    FloodWaitError, 
    AuthKeyUnregisteredError,
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PeerIdInvalidError,
    UsernameInvalidError,
    UserNotMutualContactError
)
from telethon.sessions import StringSession

# ================= 配置区域 =================
# 签到列表 (明文配置 - 你的10个Bot/频道)
SIGN_LIST: List[Tuple[str, str]] = [
    ("@sgkboxbot", "/qd"),
    ("@TBSGKBot", "/sign"),
    ("@xfhzjbot", "/qd"),
    ("@Kali_SGK_Bot", "/checkin"),
    ("@xdhz88bot", "/qd"),
    ("@Carll_Bomb_bot", "/qd"),
    ("@jdHappybot", "/qd"),
    ("@nb3344bot", "/qd"),
    ("@SGK76H", "签到"),
    ("@XFchart1", "签到")  # 新增频道签到
]

# 重试与超时配置
MAX_RETRIES = 3
DEFAULT_DELAY = 3  # 任务间隔
GLOBAL_TIMEOUT = 600  # 全局超时：10分钟
CONNECT_TIMEOUT = 20  # 连接超时
# ===========================================

def get_beijing_time():
    """获取北京时间字符串，包含极端时间检查"""
    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    beijing_now = utc_now.astimezone(beijing_tz)
    bt_str = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        year = int(beijing_now.strftime("%Y"))
        if year < 2020 or year > 2035:
            bt_str += f" [警告：系统年份 {year} 异常]"
    except:
        pass
    return bt_str

def sanitize_error(error_msg):
    """脱敏错误信息，防止泄露敏感数据"""
    if not error_msg:
        return "Unknown error"
    # 移除长字符串 (可能是 Session/Token)
    sanitized = re.sub(r'[a-zA-Z0-9_-]{20,}', '[REDACTED]', str(error_msg))
    # 移除 IP 地址
    sanitized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', sanitized)
    return sanitized[:150]

async def sign_bot(client, bot_username, command, retry_count=0):
    """
    执行单个签到任务
    策略：直接使用用户名字符串发送消息，避免 get_entity 可能的失败
    """
    if not bot_username or not command:
        return False
    
    clean_user = str(bot_username).strip()
    clean_cmd = str(command).strip()
    
    if not clean_user or not clean_cmd:
        return False

    try:
        print(f"[{get_beijing_time()}] 🔹 [尝试 {retry_count + 1}/{MAX_RETRIES}] 正在签到：{clean_user} -> 命令：{clean_cmd}", flush=True)
        
        # 🔥 核心修复：移除 timeout 参数，改用 asyncio.wait_for 包裹整个发送过程
        # Telethon 的 send_message 不支持 timeout 参数，但我们可以包裹在 wait_for 中实现超时
        await asyncio.wait_for(
            client.send_message(clean_user, clean_cmd),
            timeout=15  # 设置发送超时为 15 秒
        )
        await asyncio.sleep(2)  # 模拟真人操作
        
        print(f"[{get_beijing_time()}] ✅ [成功] {clean_user} 签到命令已发送", flush=True)
        return True
        
    except asyncio.TimeoutError:
        # 发送超时
        print(f"[{get_beijing_time()}] ❌ [失败] {clean_user}: 发送超时 (超过 15 秒)", flush=True)
        if retry_count < MAX_RETRIES:
            wait_time = 5 * (retry_count + 1)
            print(f"[{get_beijing_time()}] ↪ 检测到超时，{wait_time} 秒后重试...", flush=True)
            await asyncio.sleep(wait_time)
            return await sign_bot(client, clean_user, clean_cmd, retry_count + 1)
        return False
        
    except (PeerIdInvalidError, UsernameInvalidError, UserNotMutualContactError) as e:
        error_name = type(e).__name__
        print(f"[{get_beijing_time()}] ❌ [错误] {clean_user} 无效 (错误类型：{error_name})，跳过。", flush=True)
        return False  # 这类错误不重试
        
    except FloodWaitError as e:
        wait_time = e.seconds
        print(f"[{get_beijing_time()}] ⚠️ [Flood 限制] {clean_user} 触发限流，等待 {wait_time} 秒...", flush=True)
        await asyncio.sleep(wait_time + 5)
        if retry_count < MAX_RETRIES:
            return await sign_bot(client, clean_user, clean_cmd, retry_count + 1)
        return False
        
    except Exception as e:
        error_msg = sanitize_error(str(e))
        print(f"[{get_beijing_time()}] ❌ [失败] {clean_user}: {error_msg}", flush=True)
        
        # 智能重试：仅对网络类错误重试
        if retry_count < MAX_RETRIES:
            if any(kw in error_msg.lower() for kw in ['timeout', 'connection', 'network', 'reset', 'server', 'read', 'write', 'broken']):
                wait_time = 5 * (retry_count + 1)
                print(f"[{get_beijing_time()}] ↪ 检测到网络波动，{wait_time} 秒后重试...", flush=True)
                await asyncio.sleep(wait_time)
                return await sign_bot(client, clean_user, clean_cmd, retry_count + 1)
        return False

async def connect_with_timeout(client, timeout):
    """带超时的连接函数，防止卡死"""
    print(f"[{get_beijing_time()}] 🔌 正在尝试连接 Telegram 服务器 (超时设置：{timeout} 秒)...", flush=True)
    try:
        await asyncio.wait_for(client.connect(), timeout=timeout)
        print(f"[{get_beijing_time()}] ✅ 连接成功", flush=True)
        return True
    except asyncio.TimeoutError:
        print(f"[{get_beijing_time()}] ❌ 连接超时！超过 {timeout} 秒未响应。", flush=True)
        return False
    except Exception as e:
        print(f"[{get_beijing_time()}] ❌ 连接失败：{sanitize_error(str(e))}", flush=True)
        return False

async def main():
    print("=" * 60, flush=True)
    print(f"🚀 Telegram 自动签到 (完美版 v3 - 修复 timeout 参数)", flush=True)
    start_time = get_beijing_time()
    print(f"📅 启动时间：{start_time}", flush=True)
    print("=" * 60, flush=True)
    
    # 0. 空列表保护
    if not SIGN_LIST:
        print("❌ [严重错误] 签到列表为空！", flush=True)
        sys.exit(1)

    # 1. 环境变量预检
    api_id_str = os.environ.get("API_ID")
    api_hash = os.environ.get("API_HASH")
    session_str = os.environ.get("SESSION")
    
    # 🔥 核心修复：强制清洗 Session，去除所有换行符、回车符和首尾空格
    if session_str:
        session_str = session_str.replace("\n", "").replace("\r", "").replace(" ", "").strip()
    
    if not all([api_id_str, api_hash, session_str]):
        print("❌ [严重错误] 凭证缺失！", flush=True)
        print("请检查 GitHub Secrets 是否已设置：API_ID, API_HASH, SESSION", flush=True)
        print(f"💡 提示：SESSION 已自动清洗 (去除了换行符和空格)。", flush=True)
        sys.exit(1)
    
    # 2. API_ID 严格校验 (必须为正整数)
    try:
        api_id = int(api_id_str)
        if api_id <= 0:
            raise ValueError("API_ID 必须为正整数")
    except ValueError:
        print("❌ [严重错误] API_ID 必须是正整数，当前值无效。", flush=True)
        sys.exit(1)
    
    print("✅ 凭证格式检查通过", flush=True)
    
    # 3. 过滤无效条目 (预检查)
    valid_list = []
    for item in SIGN_LIST:
        if isinstance(item, tuple) and len(item) == 2:
            u, c = item
            if u and c and str(u).strip() and str(c).strip():
                valid_list.append(item)
    
    if not valid_list:
        print("❌ [严重错误] 没有有效的签到条目！", flush=True)
        sys.exit(1)
    
    print(f"📋 待签到任务数：{len(valid_list)}", flush=True)
    
    # 4. 创建客户端 (不自动连接)
    client = TelegramClient(
        StringSession(session_str), 
        api_id, 
        api_hash,
        connection_retries=1,
        retry_delay=1,
        auto_reconnect=False
    )
    
    success_count = 0
    fail_count = 0
    
    # 5. 尝试连接
    is_connected = await connect_with_timeout(client, CONNECT_TIMEOUT)
    
    if not is_connected:
        print("\n💡 建议：检查网络环境或重新生成 Session。", flush=True)
        sys.exit(1)
    
    try:
        # 6. 开始会话 (登录)
        print(f"[{get_beijing_time()}] 🔑 正在验证会话...", flush=True)
        await asyncio.wait_for(client.start(), timeout=CONNECT_TIMEOUT)
        print(f"[{get_beijing_time()}] ✅ 会话验证成功", flush=True)
        
        me = await client.get_me()
        display_name = me.first_name + (f" (@{me.username})" if me.username else "")
        print(f"[{get_beijing_time()}] 👤 当前账号：{display_name}", flush=True)
        
        print(f"\n[{get_beijing_time()}] 📋 开始执行签到任务...\n", flush=True)
        
        for i, (bot_username, command) in enumerate(valid_list, 1):
            print(f"[{get_beijing_time()}] [{i}/{len(valid_list)}] 处理：{str(bot_username).strip()}", flush=True)
            
            success = await sign_bot(client, bot_username, command)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            if i < len(valid_list):
                await asyncio.sleep(DEFAULT_DELAY)
        
        # 7. 统计结果
        total = len(valid_list)
        print("\n" + "=" * 60, flush=True)
        print(f"📊 签到统计结果 ({get_beijing_time()})", flush=True)
        print("=" * 60, flush=True)
        print(f"✅ 成功：{success_count} 个", flush=True)
        print(f"❌ 失败：{fail_count} 个", flush=True)
        print(f"📈 成功率：{(success_count / total * 100):.1f}%", flush=True)
        print("=" * 60, flush=True)
        
        if fail_count > 0:
            print("⚠️ 部分任务失败，请检查上方日志。", flush=True)
            print("💡 提示：如果是 'AuthKeyUnregistered'，请重新生成 Session。", flush=True)
        else:
            print("🎉 所有签到任务完成！", flush=True)
        
    except SessionPasswordNeededError:
        print(f"\n[{get_beijing_time()}] ❌ [错误] 账号需要两步验证密码！", flush=True)
        print("💡 解决方案：请在本地重新登录并生成新的 Session 字符串。", flush=True)
    except AuthKeyUnregisteredError:
        print(f"\n[{get_beijing_time()}] ❌ [错误] Session 已失效或未授权！", flush=True)
        print("💡 解决方案：请重新生成 Session 字符串并更新 GitHub Secrets。", flush=True)
    except ApiIdInvalidError:
        print(f"\n[{get_beijing_time()}] ❌ [错误] API_ID 或 API_HASH 无效！", flush=True)
        print("💡 解决方案：请检查 my.telegram.org 上的配置。", flush=True)
    except PhoneNumberInvalidError:
        print(f"\n[{get_beijing_time()}] ❌ [错误] 手机号格式错误。", flush=True)
    except Exception as e:
        print(f"\n[{get_beijing_time()}] ❌ [运行异常] {sanitize_error(str(e))}", flush=True)
    finally:
        # 8. 断开连接
        print(f"\n[{get_beijing_time()}] 🛑 正在断开连接...", flush=True)
        try:
            await asyncio.wait_for(client.disconnect(), timeout=5)
            print(f"[{get_beijing_time()}] ✅ 已断开连接", flush=True)
        except:
            pass

if __name__ == "__main__":
    try:
        # 全局超时保护：防止任何不可预见的死锁
        asyncio.run(asyncio.wait_for(main(), timeout=GLOBAL_TIMEOUT))
    except asyncio.TimeoutError:
        print(f"\n💥 程序执行超时 (超过 {GLOBAL_TIMEOUT} 秒)，强制终止。", flush=True)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户手动中断。", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序崩溃：{sanitize_error(str(e))}", flush=True)
        sys.exit(1)