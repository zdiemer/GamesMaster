"""Imports for all clients"""

from .ClientBase import (
    ClientBase,
    DatePart,
    ImmediatelyStopStatusError,
    RateLimit,
    ResponseNotOkError,
)
from .ShoppingClientBase import ShoppingClientBase, BaseResult
from .backloggd.BackloggdClient import BackloggdClient
from .game_faqs.GameFaqsClient import GameFaqsClient
from .giant_bomb.GiantBombClient import GiantBombClient
from .igdb.IgdbClient import IgdbClient
from .igdb.IgdbObject import IgdbObject
from .igdb.IgdbQuery import IgdbQuery
from .metacritic.MetacriticClient import MetacriticClient
from .moby_games.MobyGamesClient import MobyGamesClient
from .price_charting.PriceChartingClient import PriceChartingClient
from .rom_hacking.RomHackingClient import RomHackingClient
from .vg_chartz.VgChartzClient import VgChartzClient
from .gameye.GameyeClient import GameyeClient
from .game_jolt.GameJoltClient import GameJoltClient
from .wrappers import SteamWrapper, WikipediaWrapper
from .hltb.HltbClient import HltbClient
from .cooptimus.CooptimusClient import CooptimusClient
from .amazon.AmazonClient import AmazonClient
from .arcade_database.ArcadeDatabaseClient import ArcadeDatabaseClient
from .game_spot.GameSpotClient import GameSpotClient
from .vndb.VndbClient import VndbClient
from .the_cover_project.TheCoverProjectClient import TheCoverProjectClient
from .video_games_museum.VideoGamesMuseumClient import VideoGamesMuseumClient
from .generation_msx.GenerationMsxClient import GenerationMsxClient
from .ign.IgnClient import IgnClient
from .arduboy.ArduboyClient import ArduboyClient
from .arcade_history.ArcadeHistoryClient import ArcadeHistoryClient
from .flashpoint.FlashpointClient import FlashpointClient
from .thumby.ThumbyClient import ThumbyClient
from .launchbox.LaunchboxClient import LaunchboxClient
from .universal_video_games_list.UniversalVideoGamesListClient import (
    UniversalVideoGamesListClient,
)
from .the_independent_games_wiki.TheIndependentGamesWikiClient import (
    TheIndependentGamesWikiClient,
)

from .moby_games.moby_games_types import *
from .hltb.HltbResult import HltbResult
from .arcade_database.arcade_database_types import *

from .InputHelper import InputHelper
