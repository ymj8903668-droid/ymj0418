# wechat_alpha_mvp

最小可运行系统：监控微信群消息并统计股票与题材热度。

## 1. 环境准备

- Python 3.11
- PostgreSQL

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r wechat_alpha_mvp/requirements.txt
```

## 2. 配置数据库

默认连接串：

`postgresql://postgres:postgres@localhost:5432/wechat_alpha`

你也可以通过环境变量覆盖：

```bash
export DATABASE_URL='postgresql://user:pass@localhost:5432/wechat_alpha'
```

初始化表结构：

```bash
python -m wechat_alpha_mvp.database.init_db
```

## 3. 导入原始微信消息

系统读取表 `raw_wechat_messages` 的新增数据，字段如下：

- `sender`
- `group_name`
- `content`
- `sent_at`

每次只会处理 `sync_state.last_raw_id` 之后的数据。

## 4. 启动任务调度

```bash
python -m wechat_alpha_mvp.scheduler.job_runner
```

- 每 1 分钟读取新消息并做股票/题材匹配。
- 每 10 分钟更新 `topic_heat`。

## 5. 启动 API

```bash
uvicorn wechat_alpha_mvp.api.api_server:app --host 0.0.0.0 --port 8000
```

接口：

- `GET /hot_topics`
- `GET /top_speakers`
- `GET /recent_messages`
