from enum import Enum
from typing import Optional

import psycopg2

from excel_game import (
    ExcelGame,
    ExcelOwnedCondition,
    ExcelOwnedFormat,
    ExcelRegion,
    FuzzyDateType,
    Playability,
    PlayingStatus,
    TranslationStatus,
)


class CompanyType(Enum):
    PUBLISHER = 0
    DEVELOPER = 1


excel_owned_condition_map = {
    ExcelOwnedCondition.COMPLETE: 0,
    ExcelOwnedCondition.CASE_ONLY: 1,
    ExcelOwnedCondition.GAME_ONLY: 2,
    ExcelOwnedCondition.GAME_AND_BOX_ONLY: 3,
    ExcelOwnedCondition.MANUAL_ONLY: 5,
}

excel_playability_map = {
    Playability.PLAYABLE: 0,
    Playability.UNPLAYABLE: 1,
    Playability.UNKNOWN: 2,
}

excel_playing_status_map = {
    PlayingStatus.PLAYING: 0,
    PlayingStatus.STALLED: 2,
    PlayingStatus.UPCOMING: 3,
}

excel_owned_format_map = {
    ExcelOwnedFormat.DIGITAL: 0,
    ExcelOwnedFormat.BOTH: 1,
    ExcelOwnedFormat.PHYSICAL: 2,
}

excel_region_map = {
    ExcelRegion.ASIA: 0,
    ExcelRegion.AUSTRALIA: 1,
    ExcelRegion.BRAZIL: 2,
    ExcelRegion.CHINA: 3,
    ExcelRegion.GERMANY: 4,
    ExcelRegion.EUROPE: 5,
    ExcelRegion.FRANCE: 6,
    ExcelRegion.ITALY: 7,
    ExcelRegion.JAPAN: 8,
    ExcelRegion.KOREA: 9,
    ExcelRegion.NORTH_AMERICA: 10,
    ExcelRegion.SWEDEN: 11,
    ExcelRegion.SPAIN: 12,
    ExcelRegion.TAIWAN: 13,
    ExcelRegion.YUGOSLAVIA: 14,
}

excel_translation_status_map = {
    TranslationStatus.NONE: 0,
    TranslationStatus.PARTIAL: 1,
    TranslationStatus.COMPLETE: 2,
}


def __get_database_id(
    conn: psycopg2.extensions.connection, table: str, name: str
) -> Optional[int]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT id FROM games.{table} WHERE name = %s", (name,))
        result = cur.fetchone()
        return result[0] if result else None


def get_company_id(
    conn: psycopg2.extensions.connection, company_name: str
) -> Optional[int]:
    return __get_database_id(conn, "companies", company_name)


def get_franchise_id(
    conn: psycopg2.extensions.connection, franchise_name: str
) -> Optional[int]:
    return __get_database_id(conn, "franchises", franchise_name)


def get_genre_id(
    conn: psycopg2.extensions.connection, genre_name: str
) -> Optional[int]:
    return __get_database_id(conn, "genres", genre_name)


def get_platform_id(
    conn: psycopg2.extensions.connection, platform_name: str
) -> Optional[int]:
    return __get_database_id(conn, "platforms", platform_name)


def __create_with_name(
    conn: psycopg2.extensions.connection, table: str, name: str
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO games.{table} (name) VALUES (%s) RETURNING id",
            (name,),
        )
        return cur.fetchone()[0]


def __get_or_create_with_name(
    conn: psycopg2.extensions.connection, table: str, name: str
) -> int:
    existing_id = __get_database_id(conn, table, name)
    if existing_id is not None:
        return existing_id
    return __create_with_name(conn, table, name)


def create_company(conn: psycopg2.extensions.connection, company_name: str) -> int:
    return __create_with_name(conn, "companies", company_name)


def get_or_create_company(
    conn: psycopg2.extensions.connection, company_name: str
) -> int:
    return __get_or_create_with_name(conn, "companies", company_name)


def create_franchise(conn: psycopg2.extensions.connection, franchise_name: str) -> int:
    return __create_with_name(conn, "franchises", franchise_name)


def get_or_create_franchise(
    conn: psycopg2.extensions.connection, franchise_name: str
) -> int:
    return __get_or_create_with_name(conn, "franchises", franchise_name)


def create_genre(conn: psycopg2.extensions.connection, genre_name: str) -> int:
    return __create_with_name(conn, "genres", genre_name)


def get_or_create_genre(conn: psycopg2.extensions.connection, genre_name: str) -> int:
    return __get_or_create_with_name(conn, "genres", genre_name)


def __create_game_mapping(
    conn: psycopg2.extensions.connection,
    game_id: int,
    mapping_id: int,
    table_name: str,
    id_field_name: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO games.game_{table_name} (game_id, {id_field_name})
            VALUES (%s, %s)
            RETURNING id
            """,
            (game_id, mapping_id),
        )
        return cur.fetchone()[0]


def create_game_company(
    conn: psycopg2.extensions.connection,
    company_id: int,
    company_type: CompanyType,
    game_id: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games.game_companies (company_id, company_type_id, game_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (company_id, company_type.value, game_id),
        )
        return cur.fetchone()[0]


def create_game_franchise(
    conn: psycopg2.extensions.connection,
    franchise_id: int,
    game_id: int,
) -> int:
    return __create_game_mapping(
        conn, game_id, franchise_id, "franchises", "franchise_id"
    )


def create_game_genre(
    conn: psycopg2.extensions.connection,
    genre_id: int,
    game_id: int,
) -> int:
    return __create_game_mapping(conn, game_id, genre_id, "genres", "genre_id")


def create_game_completion(
    conn: psycopg2.extensions.connection, game: ExcelGame, game_id: int
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games.game_completions (
                id, game_id, played_in_vr, rating, start_date, completed_date,
                play_time, played_on_device, was_emulated, notes
                )
            OVERRIDING SYSTEM VALUE
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                game.completion_number,
                game_id,
                game.played_in_vr,
                game.rating,
                game.date_started,
                game.date_completed,
                game.completion_time,
                "Steam Deck" if game.steam_deck else None,
                game.emulated,
                game.notes,
            ),
        )
        return cur.fetchone()[0]


def create_game_ownership(
    conn: psycopg2.extensions.connection, game: ExcelGame, game_id: int
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games.game_ownerships (
                game_id, ownership_condition_type_id, purchase_date, purchase_price,
                ownership_format_type_id, notes
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s
            )
            RETURNING id
            """,
            (
                game_id,
                (
                    excel_owned_condition_map[game.owned_condition]
                    if game.owned_condition
                    else None
                ),
                game.date_purchased,
                game.purchase_price,
                (
                    excel_owned_format_map[game.owned_format]
                    if game.owned_format
                    else None
                ),
                game.notes,
            ),
        )
        return cur.fetchone()[0]


def create_game(
    conn: psycopg2.extensions.connection,
    game: ExcelGame,
    parent_game_id: Optional[int] = None,
) -> int:
    platform_id = get_platform_id(conn, game.platform.value)

    with conn.cursor() as cur:
        is_collection = (
            game.completed
            or game.completion_time is not None
            or game.date_completed is not None
        ) and game.completion_number is None

        cur.execute(
            """
            INSERT INTO games.games (
                title, platform_id, release_month, release_day, release_year, is_vr,
                is_dlc, critic_rating, user_rating, estimated_playtime, added_date, file_size,
                mame_romset, translation_status_id, release_region_id, notes, priority, is_wishlisted,
                game_playability_id, game_playing_status_id, is_collection, parent_game_id, playing_progress
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                game.title,
                platform_id,
                (
                    game.release_date.month
                    if game.release_date
                    and game.fuzzy_date in (None, FuzzyDateType.MONTH_AND_YEAR_ONLY)
                    else None
                ),
                (
                    game.release_date.day
                    if game.release_date and game.fuzzy_date is None
                    else None
                ),
                game.release_year,
                game.vr,
                game.dlc,
                game.metacritic_rating,
                game.gamefaqs_rating,
                game.estimated_playtime,
                game.date_added,
                game.file_size,
                game.mame_romset,
                (
                    excel_translation_status_map[game.translation]
                    if game.translation
                    else None
                ),
                excel_region_map[game.release_region],
                game.notes,
                game.priority,
                game.wishlisted,
                excel_playability_map[game.playability],
                (
                    excel_playing_status_map[game.playing_status]
                    if game.playing_status
                    else None
                ),
                is_collection,
                parent_game_id,
                game.playing_progress,
            ),
        )
        game_id = cur.fetchone()[0]

    publisher_id = get_or_create_company(conn, game.publisher)
    developer_id = get_or_create_company(conn, game.developer)

    create_game_company(conn, publisher_id, CompanyType.PUBLISHER, game_id)
    create_game_company(conn, developer_id, CompanyType.DEVELOPER, game_id)

    if game.franchise:
        franchise_id = get_or_create_franchise(conn, game.franchise)

        create_game_franchise(conn, franchise_id, game_id)

    genre_id = get_or_create_genre(conn, game.genre.value)

    create_game_genre(conn, genre_id, game_id)

    if game.completed and not is_collection:
        create_game_completion(conn, game, game_id)

    if game.owned:
        create_game_ownership(conn, game, game_id)

    for child_game in game.child_games:
        create_game(conn, child_game, game_id)

    return game_id


def clear_database(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM games.game_completions;
            DELETE FROM games.game_franchises;
            DELETE FROM games.game_genres;
            DELETE FROM games.game_ownerships;
            DELETE FROM games.game_companies;
            DELETE FROM games.games;
            """
        )

    conn.commit()
