import datetime
import warnings
from typing import Any, Dict, List, Optional, Tuple, Type

import openpyxl
import pandas as pd
import psycopg2
import sql_mappings
from excel_game import (
    ExcelGame,
    ExcelGameBuilder,
    FuzzyDateType,
    Playability,
    PlayingStatus,
    TranslationStatus,
)
from excel_game import (
    ExcelRegion as Region,
)
from styleframe import StyleFrame

# pass: excelloader


class ExcelLoader:
    _sf: Optional[StyleFrame] = None
    _cg_df: Optional[pd.DataFrame] = None
    _goo_df: Optional[pd.DataFrame] = None
    _games: Optional[List[ExcelGame]] = None
    _completed_games: Optional[List[ExcelGame]] = None
    _games_on_order: Optional[List[ExcelGame]] = None
    __fetch_from_postgres: bool = False

    __sheet_path: str

    __BASE_DROPBOX_FOLDER = "C:\\Users\\zachd\\Dropbox\\Video Game Lists"
    __EXCEL_SHEET_NAME = "Games Master List - Final.xlsx"

    def __init__(
        self,
        file_path: Optional[str] = None,
        eager: bool = False,
        fetch_from_postgres: bool = False,
    ):
        warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

        if file_path is None:
            file_path = f"{self.__BASE_DROPBOX_FOLDER}\\{self.__EXCEL_SHEET_NAME}"

        self.__sheet_path = file_path

        self.__fetch_from_postgres = fetch_from_postgres

        if eager:
            self.__load_games()

    def __read_excel(self, file_path: str, sheet: str = "Games") -> StyleFrame:
        return StyleFrame.read_excel(
            file_path,
            sheet_name=sheet,
            keep_default_na=False,
            read_style=True,
            use_openpyxl_styles=False,
        )

    def __get_pg_connection(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(
            dbname="games",
            user="excel_loader",
            password="excelloader",
            host="localhost",
            port=5432,
        )

    @property
    def df(self) -> pd.DataFrame:
        return self.sf.data_df

    @property
    def sf(self) -> StyleFrame:
        if self._sf is None:
            start = datetime.datetime.now()
            print(f"Loading Excel file from {self.__sheet_path}...")
            self._sf = self.__read_excel(self.__sheet_path)
            print(f"Loaded Excel file in {datetime.datetime.now() - start} seconds.")

        return self._sf

    @property
    def cg_df(self) -> pd.DataFrame:
        if self._cg_df is None:
            self._cg_df = pd.read_excel(
                self.__sheet_path,
                sheet_name="Finished Games (Adtl Metadata)",
                keep_default_na=False,
            )

        return self._cg_df

    @property
    def goo_df(self) -> pd.DataFrame:
        if self._goo_df is None:
            self._goo_df = pd.read_excel(
                self.__sheet_path,
                sheet_name="Games On Order",
                keep_default_na=False,
            )

            ws = openpyxl.load_workbook(self.__sheet_path)["Games On Order"]
            links = []
            for i in range(2, ws.max_row + 1):
                # 9th Column == Order #
                cell = ws.cell(row=i, column=9)
                if cell.hyperlink is None:
                    if len(links) < self._goo_df.shape[0]:
                        links.append(None)
                        continue
                    break
                links.append(cell.hyperlink.target)

            self._goo_df["Order Link"] = links

        return self._goo_df

    def __get_inverse_mapping(self, dictionary: dict, value: int) -> Optional[any]:
        for key, val in dictionary.items():
            if val == value:
                return key
        return None

    def __get_games_from_postgres(
        self, conn: psycopg2.extensions.connection
    ) -> list[ExcelGame]:
        start = datetime.datetime.now()
        print("Fetching games from PostgreSQL database...")
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    g.title,
                    p.name,
                    g.release_month,
                    g.release_day,
                    g.release_year,
                    g.is_vr,
                    g.is_dlc,
                    g.critic_rating,
                    g.user_rating,
                    g.estimated_playtime,
                    g.added_date,
                    g.file_size,
                    g.mame_romset,
                    ts.id,
                    r.short_name,
                    g.notes,
                    g.is_wishlisted,
                    g.game_playability_id,
                    g.game_playing_status_id,
                    gc.id,
                    gc.played_in_vr,
                    gc.rating,
                    gc.start_date,
                    gc.completed_date,
                    gc.play_time,
                    gc.played_on_device,
                    gc.was_emulated,
                    gc.notes,
                    f.name,
                    ge.name,
                    go.ownership_condition_type_id,
                    go.purchase_date,
                    go.purchase_price,
                    go.ownership_format_type_id,
                    dev.name,
                    pub.name,
                    g.playing_progress
                FROM games.games AS g
                LEFT JOIN games.platforms AS p ON g.platform_id = p.id
                LEFT JOIN games.translation_statuses AS ts ON g.translation_status_id = ts.id
                LEFT JOIN games.regions AS r ON g.release_region_id = r.id
                LEFT JOIN games.game_completions AS gc ON g.id = gc.game_id
                LEFT JOIN games.game_franchises AS gf ON g.id = gf.game_id
                LEFT JOIN games.franchises AS f ON f.id = gf.franchise_id
                LEFT JOIN games.game_genres AS gg ON g.id = gg.game_id
                LEFT JOIN games.genres AS ge ON ge.id = gg.genre_id
                LEFT JOIN games.game_ownerships AS go ON g.id = go.game_id
                LEFT JOIN games.game_companies AS dc ON g.id = dc.game_id AND dc.company_type_id = 1
                LEFT JOIN games.companies AS dev ON dev.id = dc.company_id
                LEFT JOIN games.game_companies AS pc ON g.id = pc.game_id AND pc.company_type_id = 0
                LEFT JOIN games.companies AS pub ON pub.id = pc.company_id
                """
            )
            rows = cur.fetchall()
            print(
                f"Fetched {len(rows)} games in {datetime.datetime.now() - start} seconds."
            )

            start = datetime.datetime.now()
            out = [
                ExcelGameBuilder()
                .with_title(row[0])
                .with_platform(str(row[1]))
                .with_release_date(
                    datetime.datetime(
                        year=row[4],
                        month=row[2] if row[2] is not None else 1,
                        day=row[3] if row[3] is not None else 1,
                    )
                    if row[4] is not None
                    else None
                )
                .with_vr(row[5])
                .with_dlc(row[6])
                .with_metacritic_rating(self.__none_or_type(row[7], float))
                .with_gamefaqs_rating(self.__none_or_type(row[8], float))
                .with_estimated_playtime(self.__none_or_type(row[9], float))
                .with_date_added(row[10])
                .with_file_size(self.__none_or_type(row[11], int))
                .with_mame_romset(row[12])
                .with_translation(
                    self.__get_inverse_mapping(
                        sql_mappings.excel_translation_status_map, row[13]
                    )
                    if row[13]
                    else None
                )
                .with_release_region(
                    Region(row[14]) if row[14] else Region.NORTH_AMERICA
                )
                .with_notes(row[15])
                .with_wishlisted(self.__none_or_type(row[16], bool))
                .with_playability(
                    self.__get_inverse_mapping(
                        sql_mappings.excel_playability_map, row[17]
                    )
                    if row[17]
                    else None
                )
                .with_playing_status(
                    self.__get_inverse_mapping(
                        sql_mappings.excel_playing_status_map, row[18]
                    )
                    if row[18]
                    else None
                )
                .with_completion_number(row[19])
                .with_played_in_vr(self.__none_or_type(row[20], bool))
                .with_rating(self.__none_or_type(row[21], float))
                .with_date_started(row[22])
                .with_date_completed(row[23])
                .with_completion_time(self.__none_or_type(row[24], float))
                .with_steam_deck(row[25] == "Steam Deck")
                .with_emulated(row[26])
                .with_completion_notes(row[27])
                .with_franchise(row[28])
                .with_genre(row[29])
                .with_owned_condition(
                    self.__get_inverse_mapping(
                        sql_mappings.excel_owned_condition_map, row[30]
                    )
                    if row[30]
                    else None
                )
                .with_date_purchased(row[31])
                .with_purchase_price(self.__none_or_type(row[32], float))
                .with_owned_format(
                    self.__get_inverse_mapping(
                        sql_mappings.excel_owned_format_map, row[33]
                    )
                    if row[33]
                    else None
                )
                .with_developer(row[34])
                .with_publisher(row[35])
                .with_owned(row[33] is not None)
                .with_completed(row[19] is not None or row[23] is not None)
                .with_fuzzy_date(
                    FuzzyDateType.MONTH_AND_YEAR_ONLY
                    if row[2] is not None and row[4] is None
                    else FuzzyDateType.YEAR_ONLY
                    if row[4] is not None
                    else None
                )
                .with_playing_progress(self.__none_or_type(row[36], float))
                .build()
                for row in rows
            ]
            print(
                f"Converted {len(out)} games in {datetime.datetime.now() - start} seconds."
            )
            return out

    def __load_games(self, df_override: Optional[pd.DataFrame] = None):
        self._games = []

        if self.__fetch_from_postgres:
            connection = self.__get_pg_connection()
            self._games = self.__get_games_from_postgres(connection)
            connection.close()
            return

        df = df_override if df_override is not None else self.df

        start = datetime.datetime.now()
        print(f"Loading games from {self.__sheet_path}...")
        for _, row in df.iterrows():
            self._games.append(
                ExcelGameBuilder()
                .with_title(str(row["Title"]))
                .with_platform(str(row["Platform"]))
                .with_release_date(
                    row["Release Date"].value
                    if row["Release Date"] != "Early Access"
                    else None
                )
                .with_release_region(Region(row["Release Region"].value))
                .with_publisher(str(row["Publisher"]))
                .with_developer(str(row["Developer"]))
                .with_franchise(self.__none_or_type(row["Franchise"]))
                .with_genre(str(row["Genre"]))
                .with_vr(self.__none_or_type(row["VR"], bool))
                .with_dlc(self.__none_or_type(row["DLC"], bool))
                .with_translation(
                    TranslationStatus(row["English"])
                    if row["English"] is not None and str(row["English"]).strip() != ""
                    else None
                )
                .with_owned(self.__none_or_type(row["Owned"], bool))
                .with_owned_condition(self.__none_or_type(row["Condition"]))
                .with_date_purchased(
                    row["Date Purchased"].value
                    if str(row["Date Purchased"]).strip() != ""
                    else None
                )
                .with_purchase_price(self.__none_or_type(row["Purchase Price"], float))
                .with_owned_format(self.__none_or_type(row["Format"]))
                .with_completed(bool(row["Completed"]))
                .with_date_started(
                    row["Date Started"].value
                    if str(row["Date Started"]).strip() != ""
                    else None
                )
                .with_date_completed(
                    row["Date Completed"].value
                    if str(row["Date Completed"]).strip() != ""
                    else None
                )
                .with_date_added(
                    row["Date Added"].value
                    if str(row["Date Added"]).strip() != ""
                    else None
                )
                .with_completion_time(
                    self.__none_or_type(row["Completion Time"], float)
                )
                .with_rating(self.__none_or_type(row["Rating"], float))
                .with_metacritic_rating(
                    self.__none_or_type(row["Metacritic Rating"], float)
                )
                .with_gamefaqs_rating(
                    self.__none_or_type(row["GameFAQs User Rating"], float)
                )
                .with_notes(self.__none_or_type(row["Notes"], str))
                .with_priority(self.__none_or_type(row["Priority"], int))
                .with_wishlisted(self.__none_or_type(row["Wishlisted"], bool))
                .with_estimated_playtime(
                    self.__none_or_type(row["Estimated Time"], float)
                )
                .with_playing_status(
                    PlayingStatus(row["Playing Status"])
                    if row["Playing Status"] is not None
                    and str(row["Playing Status"]).strip() != ""
                    else None
                )
                .with_playing_progress(
                    self.__none_or_type(row["Playing Progress"], float)
                )
                .with_playability(Playability(row["Playable"]))
                .with_fuzzy_date(
                    FuzzyDateType.YEAR_ONLY
                    if row["Release Date"].style.bold
                    and row["Release Date"].style.italic
                    else (
                        FuzzyDateType.MONTH_AND_YEAR_ONLY
                        if row["Release Date"].style.italic
                        else None
                    )
                )
                .with_file_size(
                    self.__none_or_type(
                        (
                            (row["File Size"] if row["File Size"] != "N/A" else 0)
                            if row["File Size"] != "?"
                            else None
                        ),
                        int,
                    )
                )
                .with_mame_romset(self.__none_or_type(row["MAME Romset"]))
                .build()
            )
        print(
            f"Loaded {len(self._games)} games in {datetime.datetime.now() - start} seconds."
        )

    @property
    def games(self) -> List[ExcelGame]:
        if self._games is None:
            self.__load_games()

        return self._games

    @property
    def completed_games(self) -> List[ExcelGame]:
        if self._completed_games is None:
            self._completed_games = []

            for _, row in self.cg_df.iterrows():
                self._completed_games.append(
                    ExcelGameBuilder()
                    .with_title(str(row["Game"]))
                    .with_platform(str(row["Platform"]))
                    .with_release_date(row["Release"])
                    .with_release_region(Region(row["Region"]))
                    .with_publisher(str(row["Publisher"]))
                    .with_developer(str(row["Developer"]))
                    .with_franchise(self.__none_or_type(row["Franchise"]))
                    .with_genre(str(row["Genre"]))
                    .with_played_in_vr(self.__none_or_type(row["VR"], bool))
                    .with_collection(self.__none_or_type(row["Collection"]))
                    .with_rating(float(row["Rating"]))
                    .with_completion_number(int(row["#"]))
                    .with_date_started(
                        row["Started"] if str(row["Started"]).strip() != "" else None
                    )
                    .with_date_completed(
                        row["Date"] if str(row["Date"]).strip() != "" else None
                    )
                    .with_completion_time(self.__none_or_type(row["Play Time"], float))
                    .with_steam_deck(self.__none_or_type(row["Steam Deck"], bool))
                    .with_emulated(self.__none_or_type(row["Emulated"], bool))
                    .with_metacritic_rating(
                        self.__none_or_type(row["Critic Score"], float)
                    )
                    .with_completion_notes(self.__none_or_type(row["Notes"]))
                    .build()
                )

                inserted = self._completed_games[-1]

                if inserted.rating is None:
                    print(f"{inserted.full_name} is missing a rating")

        return self._completed_games

    @property
    def games_on_order(self) -> List[ExcelGame]:
        if self._games_on_order is None:
            self._games_on_order = []

            for _, row in self.goo_df.iterrows():
                self._games_on_order.append(
                    ExcelGameBuilder()
                    .with_title(str(row["Title"]))
                    .with_platform(
                        str(row["Platform"]) if row["Platform"] != "TBD" else None
                    )
                    .with_order_vendor(str(row["Vendor"]))
                    .with_date_purchased(row["Ordered Date"])
                    .with_purchase_price(float(row["Price"]))
                    .with_owned_format(str(row["Format"]))
                    .with_order_status(str(row["Status"]))
                    .with_estimated_release(
                        row["Estimated Release"]
                        if row["Estimated Release"] is not None
                        and row["Estimated Release"] != "N/A"
                        else None
                    )
                    .with_order_id(str(row["Order #"]))
                    .with_order_link(str(row["Order Link"]))
                    .with_address_on_order(
                        str(row["Address on Order"])
                        if row["Address on Order"] != "N/A"
                        else None
                    )
                    .with_tracking_number(self.__none_or_type(row["Tracking #"]))
                    .build()
                )

        return self._games_on_order

    @staticmethod
    def __none_or_type(value: Optional[Any], _type: Type = str):
        return None if value is None or str(value).strip() == "" else _type(value)

    def override_sheet(self, df_override: pd.DataFrame):
        self.__load_games(df_override)

    def clear(self):
        self._sf = None
        self._cg_df = None
        self._goo_df = None
        self._games = None
        self._completed_games = None
        self._games_on_order = None

    def reload(self):
        self.clear()
        _ = self.games
        _ = self.completed_games
        _ = self.games_on_order

    def merge(self) -> Tuple[List[ExcelGame], List[Tuple[ExcelGame, str]]]:
        hashed_games: Dict[int, List[ExcelGame]] = {}
        collection_games: Dict[int, List[ExcelGame]] = {}
        collection_hashes: Dict[str, int] = {}
        errors: List[Tuple[ExcelGame, str]] = []

        def add_children(g_hash: int, g: ExcelGame):
            if g_hash in collection_games:
                g.child_games = collection_games[g_hash]

        for g in self.games:
            hashed_g = hash(g)

            if g.collection_hash_id not in collection_hashes:
                collection_hashes[g.collection_hash_id] = hashed_g
            else:
                errors.append((g, "Merged: Duplicate Collection Hash in Main Sheet"))

            if hashed_g in hashed_games:
                hashed_games[hashed_g].append(g)
                errors.append((g, "Merged: Duplicate in Main Sheet"))
            else:
                hashed_games[hashed_g] = [g]

        for g in self.completed_games:
            hashed_g = hash(g)
            if hashed_g in hashed_games:
                hashed_games[hashed_g].append(g)
            else:
                if g.collection is None:
                    errors.append((g, "Merged: Hash Found Only in Completed"))
                elif g.collection_hash_id in collection_hashes:
                    hashed_g = collection_hashes[g.collection_hash_id]
                    if hashed_g in collection_games:
                        collection_games[hashed_g].append(g)
                    else:
                        collection_games[hashed_g] = [g]
                    continue
                else:
                    errors.append((g, "Merged: Collection Hash Not Found"))

        output_games: List[ExcelGame] = []

        for g_hash, games in hashed_games.items():
            if len(games) == 1:
                add_children(g_hash, games[0])
                output_games.append(games[0])
                continue

            if len(games) > 2:
                raise ValueError(
                    f"Unexpectedly found more than 2 games: {', '.join(g.title for g in games)}"
                )

            combined_game = ExcelGame()

            for g in games:
                combined_game = ExcelGameBuilder().merge(g, combined_game)

            add_children(g_hash, combined_game)

            output_games.append(combined_game)

        return (output_games, errors)

    def export(self, conn: Optional[psycopg2.extensions.connection] = None):
        if conn is None:
            conn = self.__get_pg_connection()

        games, errors = self.merge()

        if any(errors):
            raise RuntimeError(
                f"Errors found during merge: {', '.join(f'{g.title}: {e}' for g, e in errors)}"
            )

        for game in games:
            print(f"Inserting game: {game.full_name}")
            sql_mappings.create_game(conn, game)
            conn.commit()

        conn.close()

    def clean_export(self):
        conn = self.__get_pg_connection()
        sql_mappings.clear_database(conn)
        self.export(conn)
