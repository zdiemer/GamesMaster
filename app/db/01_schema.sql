CREATE TABLE IF NOT EXISTS games (
    game_id     CHAR(36)                NOT NULL,
    title       VARCHAR(256)            NOT NULL,
    PRIMARY KEY (game_id)
);
