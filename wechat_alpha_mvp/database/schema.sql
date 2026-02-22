CREATE TABLE IF NOT EXISTS raw_wechat_messages (
    id BIGSERIAL PRIMARY KEY,
    wx_msg_id TEXT UNIQUE,
    sender TEXT NOT NULL,
    group_name TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    raw_id BIGINT UNIQUE REFERENCES raw_wechat_messages(id),
    sender TEXT NOT NULL,
    group_name TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);

CREATE TABLE IF NOT EXISTS message_stock_map (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    matched_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(message_id, stock_code)
);

CREATE TABLE IF NOT EXISTS message_topic_map (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    topic_name TEXT NOT NULL,
    matched_keyword TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(message_id, topic_name)
);

CREATE TABLE IF NOT EXISTS topic_heat (
    id BIGSERIAL PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    topic_name TEXT NOT NULL,
    mention_count INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(window_start, window_end, topic_name)
);

CREATE TABLE IF NOT EXISTS sync_state (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    last_raw_id BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO sync_state(id, last_raw_id)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;
