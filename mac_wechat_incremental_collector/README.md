# mac_wechat_incremental_collector

用于 macOS 的微信 SQLite 增量采集模块，可长期运行并写入标准化数据库（SQLite 或 PostgreSQL）。

## 功能
- 扫描多个源数据库（如 `MSG0.db`, `MSG1.db`, ...）
- 复制源库后查询，避免与微信进程锁冲突
- 通过 `msg_id > last_processed_id` 做增量抓取
- 使用 `sha256(sender + content + create_time)` 去重
- 标准化写入 `messages`
- 记录每个源数据库的处理进度 `collector_state`
- 文件日志 + 控制台日志，支持长期运行

## 模块
- `db_reader.py`：读取源 SQLite 并标准化
- `message_deduper.py`：哈希去重
- `db_writer.py`：写入 SQLite / PostgreSQL
- `job_runner.py`：循环调度与 APScheduler 模式
- `config.py`：环境变量配置
- `logger.py`：日志器

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install psycopg[binary] apscheduler
```

默认输出到 SQLite：`collector_output.db`。

### 运行（自带循环）
```bash
python -m mac_wechat_incremental_collector.job_runner
```

### APScheduler 模式
```python
from mac_wechat_incremental_collector.job_runner import run_with_apscheduler
run_with_apscheduler()
```

## 关键环境变量
- `WECHAT_DB_DIR`：微信数据库根目录
- `WECHAT_DB_GLOB`：数据库扫描模式，默认 `**/MSG*.db`
- `WECHAT_SOURCE_TABLE`：消息表名，默认 `message_table`
- `WECHAT_MSG_ID_COL`/`WECHAT_SENDER_COL`/`WECHAT_GROUP_COL`/`WECHAT_CONTENT_COL`/`WECHAT_CREATE_TIME_COL`
- `TARGET_DB_TYPE`：`sqlite` 或 `postgres`
- `TARGET_SQLITE_PATH`：SQLite 输出文件
- `TARGET_POSTGRES_DSN`：PostgreSQL 连接串
- `RUN_INTERVAL_SECONDS`：调度间隔（建议 60~300）
- `LOG_FILE`/`LOG_LEVEL`

## 标准化输出字段
- `msg_id`
- `sender`
- `group_name`
- `content`
- `create_time`
- `message_hash`
- `source_db`
- `source_type = "db_read"`
