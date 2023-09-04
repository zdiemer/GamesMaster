-- Title,Platform,Release Date,Release Region,Publisher,Developer,Franchise,
-- Genre,VR,DLC,English,Owned,Condition,Date Purchased, Purchase Price ,Format,
-- Completed,Date Completed,Completion Time,Rating,Metacritic Rating,
-- GameFAQs User Rating,Notes,Priority,Wishlisted,Estimated Time,Playing Status,
-- Release Year,Weighted Score,Composite Score,My Score

CREATE TABLE IF NOT EXISTS games (
    game_id         CHAR(36)                NOT NULL,
    title           VARCHAR(256)            NOT NULL,
    platform        VARCHAR(256)            NOT NULL,
    release_date    DATE,
    early_access    BOOLEAN                 DEFAULT FALSE,
    release_region  VARCHAR(16)             NOT NULL,
    publisher       VARCHAR(256)            NOT NULL,
    developer       VARCHAR(256)            NOT NULL,
    franchise       VARCHAR(256)            DEFAULT '',
    genre           VARCHAR(256)            NOT NULL,
    vr              BOOLEAN                 NOT NULL,
    dlc             BOOLEAN                 NOT NULL,
    english         INT                     DEFAULT 0,
    owned           BOOLEAN                 DEFAULT false,
    owned_condition VARCHAR(256)            DEFAULT '',
    date_purchased  DATE,
    purchase_price  DECIMAL,
    purchase_format ENUM('digital', 'physical', 'both'),
    completed       BOOLEAN                 DEFAULT false,
    date_completed          DATE,
    completion_time         DECIMAL,
    rating                  DECIMAL,
    metacritic_rating       DECIMAL,
    gamefaqs_user_rating    DECIMAL,
    notes                   VARCHAR(256)                      DEFAULT '',
    priority                INT                            DEFAULT 0,
    wishlisted              BOOLEAN                      DEFAULT false,
    estimated_time DECIMAL,
    playing_status INT                      DEFAULT 0,
    release_year YEAR                       NOT NULL,
    weighted_score DECIMAL,
    composite_score DECIMAL,
    z_score DECIMAL,
    PRIMARY KEY (game_id)
);
