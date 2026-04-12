from __future__ import annotations

import unidecode
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from bs4 import BeautifulSoup

from clients import ClientBase
from config import Config
from excel_game import ExcelGame, ExcelPlatform
from game_match import GameMatch
from match_validator import MatchValidator


class ArcadeHistoryClient(ClientBase):
    supported_platforms: Dict[ExcelPlatform, List[str]] = {
        ExcelPlatform._3DO: ["panasonic 3do cd"],
        ExcelPlatform.ACORN_ARCHIMEDES: [
            "acorn archimedes rom",
            "acorn archimedes disk",
        ],
        ExcelPlatform.ACORN_ATOM: [
            "acorn atom rom",
            "acorn atom disk",
            "acorn atom cass.",
            "acorn atom type-in",
        ],
        ExcelPlatform.ACORN_ELECTRON: [
            "acorn bbc/electron rom",
            "acorn bbc/electron cass.",
            "acorn electron 3.5in. disk",
            "acorn electron 5.25in. disk",
            "acorn electron rom",
            "acorn electron cart.",
            "acorn electron cass.",
        ],
        ExcelPlatform.ACTION_MAX: ["wow action max vhs"],
        ExcelPlatform.AMSTRAD_CPC: [
            "amstrad cpc/atari 800 cass.",
            "amstrad cpc/c64 cass.",
            "amstrad cpc/pcw disk",
            "amstrad cpc/pcw/spectrum+3 disk",
            "amstrad cpc/spectrum+3 disk",
            "amstrad cpc/zx spectrum cass.",
            "amstrad cpc/zx spectrum disk",
            "amstrad cpc 464 disk",
            "amstrad cpc 6128 disk",
            "amstard cpc cass.",
            "amstrad cpc pack.",
            "amstrad cpc type-in",
        ],
        ExcelPlatform.AMSTRAD_PCW: [
            "amstrad cpc/pcw disk",
            "amstrad cpc/pcw/spectrum+3 disk",
            "amstrad pcw soft.",
            "amstrad pcw16 disk",
        ],
        ExcelPlatform.ANDROID: ["google play pack."],
        ExcelPlatform.APPLE_II: [
            "apple ii/c64 disk",
            "apple ii/c64/ibm pc disk",
            "apple ii/ibm pc disk",
            "apple ii/ibm pc/mac disk",
            "apple ii/pet/trs-80 disk",
            "apple ii/trs-80 disk",
            "atari 800/apple ii disk",
            "atari 800/apple ii/pet cass.",
            "atari 800/apple ii/pet/trs-80 cass.",
            "atari 800/apple ii/trs-80 cass.",
            "apple ii 5.25 disk",
            "apple ii cass.",
            "apple ii type-in",
            "apple iic+ 3.5in. disk",
        ],
        ExcelPlatform.APPLE_IIGS: ["apple iigs disk"],
        ExcelPlatform.APPLE_III: ["apple iii disk"],
        ExcelPlatform.ARCADE: [
            "arcade video game",
            "arcade video game kit",
            "arcadia super select board",
            "brezzasoft crystal system cart.",
            "cd express cubo cd32 disc",
            "ces galaxy games cart.",
            "capcom cps-ii cart.",
            "capcom cps-iii kit",
            "century cvs mod.",
            "deco cass.",
            "data east mlc cart.",
            "exa arcadia cart.",
            "exidy max-a-flex cart.",
            "gaelco modular system card",
            "gun game (video)",
            "igs pgm cart.",
            "igs pgm2 cart.",
            "igs pgm3 cart.",
            "jaleco mega system 32 cart.",
            "kaneko super nova cart.",
            "konami bubble system cart.",
            "konami python 2 dvd",
            "konami system 573 disc+cart.",
            "lazer-tron vrs disc",
            "magnet system disk",
            "namco system 246 dvd-rom",
            "namco system 256 dvd-rom",
            "nichibutsu high rate dvd",
            "nintendo playchoice-10 cart.",
            "nintendo super system cart.",
            "redemption game (video)",
            "snk hyper neogeo 64 cart.",
            "snk neo-geo mvs cart.",
            "sammy atomiswave cart.",
            "sega chihiro dvd-rom",
            "sega chihiro gd-rom",
            "sega chihiro flashcard kit",
            "sega lindbergh blue dvd-rom",
            "sega lindbergh red dvd-rom",
            "sega lindbergh yellow dvd-rom",
            "sega mega play cart.",
            "sega mega-tech cart.",
            "sega naomi 2 gd-rom",
            "sega naomi 2 cart.",
            "sega naomi gd-rom",
            "sega naomi cart.",
            "sega ringedge dvd-rom",
            "sega ringwide dvd-rom",
            "sega st-v cart.",
            "sega system 24 disk",
            "sega triforce gd-rom",
            "sega triforce cart.",
            "seta aleck64 cart.",
            "simulator (non-coin game)",
            "tourvision cart.",
            "taito f3 cart.",
            "taito g-net card",
            "taito nesicaxlive pack.",
            "taito nesicaxlive2 pack.",
            "v.r. game",
        ],
        ExcelPlatform.ARCADIA_2001: [
            "arcadia 2001 cart.",
        ],
        ExcelPlatform.ATARI_2600: [
            "atari 2600 gameline pack.",
            "atari 2600 cart.",
            "atari 2800 cart.",
            "starpath supercharger cart.",
        ],
        ExcelPlatform.ATARI_5200: [
            "atari 5200 cart.",
        ],
        ExcelPlatform.ATARI_7800: [
            "atari 7800 cart.",
        ],
        ExcelPlatform.ATARI_8_BIT: [
            "amstrad cpc/atari 800 cass.",
            "atari 800/apple ii disk",
            "atari 800/apple ii/pet cass.",
            "atari 800/apple ii/pet/trs-80 cass.",
            "atari 800/apple ii/trs-80 cass.",
            "atari 800/c64 cass.",
            "atari 800/c64 disk",
            "atari 800/c64/coco/vic-20 cass.",
            "atari 800/c64/coco/vic-20/timex cass.",
            "atari 800/c64/pet/trs-80 cass.",
            "atari 800/c64/trs-80 cass.",
            "atari 800/c64/trs-80/ti99 cass.",
            "atari 800/c64/trs-80/vic-20 cass.",
            "atari 800/c64/vic-20 cass.",
            "atari 800/pet cass.",
            "atari 800/pet/trs-80/vic-20 cass.",
            "atari 800/trs-80 cass.",
            "atari 800/trs-80 disk",
            "atari 800/trs-80/coco cass.",
            "atari 800/vic-20 cass.",
            "atari 400/800 cart.",
            "atari 400/800 cass.",
            "atari 400/800 disk",
            "atari 400/800 type-in",
            "atari xe cart.",
        ],
        ExcelPlatform.ATARI_JAGUAR: ["atari jaguar cart."],
        ExcelPlatform.ATARI_LYNX: ["atari lynx cart."],
        ExcelPlatform.ATARI_ST: [
            "atari st/amiga disk",
            "atari st/amiga/pc disk",
            "atari st cart.",
            "atari st disk",
            "atari st pack.",
            "atari st type-in",
        ],
        ExcelPlatform.BANDAI_PIPPIN: ["bandai pippin cd"],
        ExcelPlatform.BBC_MICRO: [
            "acorn bbc/electron rom",
            "acorn bbc/electron cass.",
            "acorn bbc/zx spectrum cass.",
            "acorn bbc hybrid music system disk",
            "acorn bbc master cart.",
            "acorn bbc master cass.",
            "acorn bbc master compact disk",
            "acorn bbc master disk",
            "acorn bbc master w/ 80186 co-proc. disk",
            "acorn bbc micro a cass.",
            "acorn bbc micro b disk",
            "acorn bbc micro b type-in",
            "acorn bbc rom",
            "acorn bbc w/ 32016 co-proc. disk",
            "acorn bbc w/ 6502 2nd proc. disk",
            "acorn bbc w/ 68000 co-proc. disk",
            "acorn bbc w/ arm co-proc. disk",
            "acorn bbc w/ z80 2nd proc. disk",
            "bbc bridge companion cart.",
            "acorn bbc micro hdd",
        ],
        ExcelPlatform.BREW: ["mobile phone", "mobile game"],
        ExcelPlatform.BROWSER: [
            "3dvia player game",
            "adobe flash game",
            "adobe shockwave game",
            "html game",
            "java game",
            "microsoft silverlight game",
            "unity webgl game",
        ],
        ExcelPlatform.BS_X: ["nintendo satellaview bs pack."],
        ExcelPlatform.CASIO_LOOPY: ["casio loopy cart."],
        ExcelPlatform.COLECO_ADAM: [
            "coleco adam cart.",
            "coleco adam cass.",
            "coleco adam disk",
        ],
        ExcelPlatform.COLECOVISION: ["colecovision cart."],
        ExcelPlatform.COMMODORE_64: [
            "amstrad cpc/c64 cass.",
            "apple ii/c64 disk",
            "apple ii/c64/ibm pc disk",
            "atari 800/c64 cass.",
            "atari 800/c64 disk",
            "atari 800/c64/coco/vic-20 cass.",
            "atari 800/c64/coco/vic-20/timex cass.",
            "atari 800/c64/pet/trs-80 cass.",
            "atari 800/c64/trs-80 cass.",
            "atari 800/c64/trs-80/ti99 cass.",
            "atari 800/c64/trs-80/vic-20 cass.",
            "atari 800/c64/vic-20 cass.",
            "commodore c16/c64 cass.",
            "commodore c64/ibm pc disk",
            "commodore c64/msx cass.",
            "commodore c64/msx disk",
            "commodore c64/trs-80 cass.",
            "commodore c64/trs-80 disk",
            "commodore c64/vic-20 cass.",
            "commodore c64/zx cass.",
            "commodore c64 cart.",
            "commodore c64 cass.",
            "commodore c64 disk",
            "commodore c64 pack.",
            "commodore c64 type-in",
            "commodore c64 vinyl",
        ],
        ExcelPlatform.COMMODORE_AMIGA: [
            "atari st/amiga disk",
            "atari st/amiga/pc disk",
            "commodore amiga 1000 disk",
            "commodore amiga 1200 disk",
            "commodore amiga 3000 disk",
            "commodore amiga 500 disk",
            "commodore amiga 500+ disk",
            "commodore amiga 600hd disk",
            "commodore amiga unix disk",
            "commodore amiga type-in",
        ],
        ExcelPlatform.COMMODORE_AMIGA_CD32: ["commodore amiga cd32 disc"],
        ExcelPlatform.COMMODORE_PET: [
            "apple ii/pet/trs-80 disk",
            "atari 800/apple ii/pet cass.",
            "atari 800/apple ii/pet/trs-80 cass.",
            "atari 800/c64/pet/trs-80 cass.",
            "atari 800/pet cass.",
            "atari 800/pet/trs-80/vic-20 cass.",
            "commodore cbm-ii disk",
            "commodore pet rom",
            "commodore pet cass.",
            "commodore pet disk",
            "commodore pet type-in",
            "commodore superpet disk",
            "commodore pet hdd",
        ],
        ExcelPlatform.COMMODORE_PLUS_4: [
            "commodore c16/c64 cass.",
            "commodore c16/msx cass.",
            "commodore c16/vic-20 cass.",
            "commodore c16 plus/4 cart.",
            "commodore c16 plus/4 cass.",
            "commodore c16 plus/4 disk",
            "commodore c16 cass.",
            "commodore c16 disk",
        ],
        ExcelPlatform.COMMODORE_VIC_20: [
            "atari 800/c64/coco/vic-20 cass.",
            "atari 800/c64/coco/vic-20/timex cass.",
            "atari 800/c64/trs-80/vic-20 cass.",
            "atari 800/c64/vic-20 cass.",
            "atari 800/pet/trs-80/vic-20 cass.",
            "atari 800/vic-20 cass.",
            "commodore c16/vic-20 cass.",
            "commodore c64/vic-20 cass.",
            "commodore vic-20/zx cass.",
            "commodore vic-20 cart.",
            "commodore vic-20 cass.",
            "commodore vic-20 disk",
            "commodore vic-20 type-in",
        ],
        ExcelPlatform.DEDICATED_CONSOLE: [
            "handheld game",
            "table top game",
            "watch game",
            "computer (dedicated)",
            "console (dedicated)",
            "console (handheld)",
        ],
        ExcelPlatform.DOJA: ["mobile game: docomo i-mode pack."],
        ExcelPlatform.DRAGON_32_64: [
            "dragon 64 flex disk",
            "dragon 64 os-9 disk",
            "dragon alpha disk",
            "dragon beta disk",
            "dragon cart.",
            "dragon cass.",
            "dragon disk",
            "dragon type-in",
        ],
        ExcelPlatform.DSIWARE: ["nintendo ds pack."],
        ExcelPlatform.DVD_PLAYER: ["disc player (dvd)", "dvd player game"],
        ExcelPlatform.EPOCH_SUPER_CASSETTE_VISION: [
            "epoch super cassette vision cart."
        ],
        ExcelPlatform.E_READER: ["nintendo gba e-card"],
        ExcelPlatform.EVERCADE: ["blaze evercade cart."],
        ExcelPlatform.EXEN: ["mobile phone", "mobile game"],
        ExcelPlatform.EXIDY_SORCERER: [
            "exidy sorcerer cart.",
            "exidy sorcerer cass.",
            "exidy sorcerer disk",
        ],
        ExcelPlatform.FAMICOM_DISK_SYSTEM: ["nintendo famicom disk"],
        ExcelPlatform.FM_TOWNS: [
            "nec pc-98/fujitsu fm towns cd",
            "nec pc-9801/fm-towns disk",
            "nec pc-9801/sharp x68000/fm-towns disk",
            "pc ms-windows/macintosh/fm-towns cd",
            "fujitsu fm towns cd",
            "fujitsu fm towns disk",
            "fujitsu fm towns type-in",
        ],
        ExcelPlatform.FM_7: [
            "nec pc-8801/8001/6001/fm7/x1",
            "nec pc-8801/fm-7 5.25in. disk",
            "nec pc-8801/fm-7 cass.",
            "fujitsu fm-7 3.5in. disk",
            "fujitsu fm-7 5.25in. disk",
            "fujitsu fm-7 cass.",
            "fujitsu fm-7 type-in",
            "fujitsu fm-77av disk",
            "fujitsu fm-77av type-in",
        ],
        ExcelPlatform.GALAKSIJA: ["galaksija cass."],
        ExcelPlatform.GAMATE: ["gamate cart."],
        ExcelPlatform.GAME_BOY: [
            "nintendo game boy cart.",
        ],
        ExcelPlatform.GAME_BOY_ADVANCE: ["nintendo gba cart."],
        ExcelPlatform.GAME_BOY_COLOR: [
            "nitnendo game boy color cart.",
        ],
        ExcelPlatform.GAME_COM: ["tiger game.com cart."],
        ExcelPlatform.GAMEPARK_32: ["gamepark gp32 cart."],
        ExcelPlatform.GP2X_CAANOO: ["gamepark gp2x caanoo card"],
        ExcelPlatform.GP2X_WIZ: ["gamepark gp2x wiz cart."],
        ExcelPlatform.HARTUNG_GAME_MASTER: ["hartung game master cart."],
        ExcelPlatform.HYPERSCAN: ["mattel hyperscan cd", "mattle hyperscan rfid card"],
        ExcelPlatform.INTELLIVISION: [
            "mattel intellivision ecs cart.",
            "mattel intellivision cart.",
        ],
        ExcelPlatform.IOS: ["apple store pack."],
        ExcelPlatform.IPOD: ["apple store pack."],
        ExcelPlatform.J2ME: ["mobile phone", "mobile game"],
        ExcelPlatform.LASERDISC: ["laser  videodisc game"],
        ExcelPlatform.MAC_OS: [
            "apple macos pack.",
            "apple macintosh cd",
            "apple macintosh dvd",
            "apple macintosh hd disk",
            "apple macintosh disk",
        ],
        ExcelPlatform.MAGNAVOX_ODYSSEY_2: ["magnavox odyssey² cart."],
        ExcelPlatform.MAINFRAME: ["basic soft. type-in", "dec pdp-10 soft."],
        ExcelPlatform.MATTEL_AQUARIUS: [
            "mattel aquarius cart.",
            "mattel aquarius cass.",
        ],
        ExcelPlatform.MEGA_DUCK: ["mega duck cart."],
        ExcelPlatform.MICROVISION: ["mb microvision game"],
        ExcelPlatform.MONON_COLOR: ["m&d monon color cart."],
        ExcelPlatform.MOPHUN: ["mobile phone", "mobile game"],
        ExcelPlatform.MSX: [
            "commodore c16/msx cass.",
            "commodore c64/msx cass.",
            "commodore c64/msx disk",
            "msx 3.5in disk",
            "msx 5.25in disk",
            "msx bee card",
            "msx softcard",
            "msx cart.",
            "msx cass.",
            "msx pack",
            "msx type-in",
            "yamaha msx mini-cart",
        ],
        ExcelPlatform.MSX_TURBO_R: ["msx turbo-r cart", "msx turbo-r disk"],
        ExcelPlatform.MSX2: [
            "msx 2 cart.",
            "msx 2 cass.",
            "msx 2 disk",
            "msx 2 type-in",
            "msx 2+ disk",
            "msx 2+ type-in",
        ],
        ExcelPlatform.N_GAGE: ["nokia n-gage card"],
        ExcelPlatform.NEC_PC_6001: [
            "nec pc-8801/8001/6001/fm7/x1",
            "nec pc-6001 series cart.",
            "nec pc-6001 series cass.",
            "nec pc-6001 series disk",
            "nec pc-6001 type-in",
            "nec pc-6001mkii cass.",
            "nec pc-6001mkii disk",
            "nec pc-6001mkii type-in",
            "nec pc-6001mkiisr cass.",
            "nec pc-6001mkiisr disk",
            "nec pc-6001mkiisr type-in",
            "nec pc-6601 series disk",
            "nec pc-6601sr disk",
        ],
        ExcelPlatform.NEC_PC_8801: [
            "nec pc-8801/8001/6001/fm7/x1",
            "nec pc-8801/fm-7 5.25in. disk",
            "nec pc-8801/fm-7 cass.",
            "nec pc-8801/sharp x1 disk",
            "nec pc-8801/sharp x1/mz-2200 disk",
            "nec pc-8000 disk",
            "nec pc-8001 cass.",
            "nec pc-8001 disk",
            "nec pc-8001 type-in",
            "nec pc-8001mkii cass.",
            "nec pc-8001mkii disk",
            "nec pc-8001mkii type-in",
            "nec pc-8001mkiisr cass.",
            "nec pc-8001mkiisr disk",
            "nec pc-8001mkiisr type-in",
            "nec pc-8201 cart.",
            "nec pc-8201 cass.",
            "nec pc-8201 type-in",
            "nec pc-88 va disk",
            "nec pc-88 va type-in",
            "nec pc-8801 series 8in. disk",
            "nec pc-8801 series cass.",
            "nec pc-8801 series disk",
            "nec pc-8801 series type-in",
            "nec pc-8801mc cd",
            "nec pc-8801mkii cass.",
            "nec pc-8801mkii disk",
            "nec pc-8801mkiisr cass.",
            "nec pc-8801mkiisr disk",
            "nec pc-8801mkiisr type-in",
            "nec pc-9801/pc-8801 disk",
            "sharp x68000/nec pc-88va disk",
        ],
        ExcelPlatform.NEC_PC_9801: [
            "nec pc-98/fujitsu fm towns cd",
            "nec pc-98/ms-dos 3.5in.disk",
            "nec pc-98/ms-dos 5.25in.disk",
            "nec pc-98/ms-windows cd",
            "nec pc-9801/fm-towns disk",
            "nec pc-9801/pc-8801 disk",
            "nec pc-9801/sharp x68000 disk",
            "nec pc-9801/sharp x68000/fm-towns disk",
            "nec pc-98 note 3.5in. disk",
            "nec pc-9801 series 3.5in. disk",
            "nec pc-9801 series 5.25in. disk",
            "nec pc-9801 series cass.",
            "nec pc-9801 series type-in",
            "nec pc-9821 cd",
        ],
        ExcelPlatform.NEO_GEO: ["snk neo-geo aes cart."],
        ExcelPlatform.NEO_GEO_CD: ["snk neo-geo cd"],
        ExcelPlatform.NEO_GEO_POCKET: ["snk neo-geo pocket cart."],
        ExcelPlatform.NEO_GEO_POCKET_COLOR: ["snk neo-geo pocket color cart."],
        ExcelPlatform.NES: [
            "nintendo famicom basic type-in",
            "nintendo famicom datach cart.",
            "nintendo famicom karaoke studio cart.",
            "nintendo famicom konami qtai cart.",
            "nintendo famicom nantettatte baseball cart.",
            "nintendo famicom cart.",
            "nintendo nes aladdin cart.",
            "nintendo nes ntsc cart.",
            "nintendo nes pal-a cart.",
            "nintendo nes pal-b cart.",
            "nintendo nes pal-m cart.",
        ],
        ExcelPlatform.NINTENDO_3DS: ["nintendo 3ds cart.", "nintendo 3ds pack."],
        ExcelPlatform.NINTENDO_64: [
            "lodgenet gateway system (n64) pack.",
            "nintendo 64 cart.",
        ],
        ExcelPlatform.NINTENDO_64DD: ["nintendo 64dd game"],
        ExcelPlatform.NINTENDO_DS: ["nintendo ds cart."],
        ExcelPlatform.NINTENDO_GAMECUBE: ["nintendo gamecube disc"],
        ExcelPlatform.NINTENDO_POKEMON_MINI: ["nintendo pokémon mini game"],
        ExcelPlatform.NINTENDO_SWITCH: [
            "nintendo switch cart.",
            "nintendo switch pack.",
        ],
        ExcelPlatform.NINTENDO_SWITCH_2: [
            "nintendo switch 2 cart.",
            "nintendo switch 2 pack.",
        ],
        ExcelPlatform.NINTENDO_WII: ["nintendo wii disc"],
        ExcelPlatform.NINTENDO_WII_U: [
            "nintendo wii u disc",
            "nintendo wii u eshop pack.",
        ],
        ExcelPlatform.NUON: ["samsung nuon disc"],
        ExcelPlatform.OCULUS_QUEST: ["meta quest pack."],
        ExcelPlatform.ORIC: [
            "thomson mo5/oric cass.",
            "zx81/spectrum/oric/atmos/laser 200/to7 cass.",
            "tangerine oric 1 jasmin disk",
            "tangerine oric 1 microdisc disk",
            "tangerine oric 1 cass.",
            "tangerine oric 1 type-in",
        ],
        ExcelPlatform.OS_2: ["pc/os/2 pack."],
        ExcelPlatform.PALM_OS: ["palm os soft."],
        ExcelPlatform.PC: [
            "nec pc-98/ms-dos 3.5in.disk",
            "nec pc-98/ms-dos 5.25in.disk",
            "nec pc-98/ms-windows cd",
            "pc ms-windows/macintosh cd",
            "pc ms-windows/macintosh dvd",
            "pc ms-windows/macintosh/cd-i cd",
            "pc ms-windows/macintosh/fm-towns cd",
            "pc ms-windows/x68k cd",
            "pc/ms-windows 3.5in. disk",
            "pc/ms-windows 5.25+3.5in. disk",
            "pc/ms-windows cd",
            "pc/ms-windows dvd",
            "pc/ms-windows microsoft store pack.",
            "pc/ms-windows pack.",
        ],
        ExcelPlatform.PC_FX: ["nec pc-fx game"],
        ExcelPlatform.PHILIPS_CD_I: [
            "pc ms-windows/macintosh/cd-i cd",
            "phillips cd-i disc",
        ],
        ExcelPlatform.PIONEER_LASERACTIVE: ["pioneer laseractive ld-rom"],
        ExcelPlatform.PLAYSTATION: [
            "sony playstation ntsc-j cd-rom",
            "sony playstation ntsc-u cd-rom",
            "sony playstation pal cd-rom",
        ],
        ExcelPlatform.PLAYSTATION_2: ["sony playstation 2 dvd-rom"],
        ExcelPlatform.PLAYSTATION_3: ["sony playstation 3 blu-ray"],
        ExcelPlatform.PLAYSTATION_4: [
            "sony psn: ps4 pack.",
            "sony playstation 4 blu-ray",
            "sony playstation vr blu-ray",
        ],
        ExcelPlatform.PLAYSTATION_5: [
            "sony psn: ps5 pack.",
            "sony playstation 5 blu-ray",
        ],
        ExcelPlatform.PLAYSTATION_NETWORK: [
            "sony psn: ps4 pack.",
            "sony psn: psone classics pack.",
            "sony psn: shodai ps archives pack.",
            "sony psn: ps vita pack.",
            "sony psn: psp pack.",
        ],
        ExcelPlatform.PLAYSTATION_PORTABLE: ["sony psn: psp pack.", "sony psp umd"],
        ExcelPlatform.PLAYSTATION_VITA: [
            "sony ps vita game",
            "sony psn: ps vita pack.",
        ],
        ExcelPlatform.R_ZONE: ["tiger electronic r-zone cart."],
        ExcelPlatform.SEGA_32X: [
            "sega cd 32x game",
            "sega genesis 32x cart.",
            "sega mega drive 32x cart.",
            "sega mega-cd 32x game",
            "sega super 32x cart.",
        ],
        ExcelPlatform.SEGA_CD: [
            "sega cd",
            "sega cd 32x game",
            "sega mega-cd",
            "sega mega-cd 32x game",
        ],
        ExcelPlatform.SEGA_DREAMCAST: ["sega dreamcast cd", "sega dreamcast mil-cd"],
        ExcelPlatform.SEGA_GAME_GEAR: ["sega game gear cart."],
        ExcelPlatform.SEGA_GENESIS: ["sega genesis cart.", "sega mega drive cart."],
        ExcelPlatform.SEGA_MASTER_SYSTEM: [
            "sega master system card",
            "sega master system cart.",
        ],
        ExcelPlatform.SEGA_PICO: [
            "sega beena cart.",
            "sega pico game",
            "sega sawatte pico book",
        ],
        ExcelPlatform.SEGA_SATURN: ["sega saturn cd-roim", "sega saturn cart."],
        ExcelPlatform.SEGA_SG_1000: ["sega sg-1000 game"],
        ExcelPlatform.SHARP_X1: [
            "nec pc-8801/8001/6001/fm7/x1",
            "nec pc-8801/sharp x1 disk",
            "nec pc-8801/sharp x1/mz-2200 disk",
            "sharp mz-2000/x1 cass.",
            "sharp mz-2000/x1 disk",
            "sharp x1 5.25in. disk",
            "sharp x1 turbo type-in",
            "sharp x1 cass.",
            "sharp x1 type-in",
            "sharp x1-d 3in. disk",
        ],
        ExcelPlatform.SHARP_X68000: [
            "nec pc-9801/sharp x68000 disk",
            "nec pc-9801/sharp x68000/fm-towns disk",
            "pc ms-windows/x68k cd",
            "sharp x68000/nec pc-88va disk",
            "sharp x68000 series 3.5in. disk",
            "sharp x68000 series 5.25in. disk",
            "sharp x68000 series cd",
            "sharp x68000 type-in",
        ],
        ExcelPlatform.SNES: [
            "lodgenet gateway system (snes) pack.",
            "nintendo super famicom box cart.",
            "nintendo super famicom sufami turbo cart.",
            "nintendo super famicom cart.",
            "nintendo super nes cart.",
        ],
        ExcelPlatform.SUPER_ACAN: ["funtech super a-can cart."],
        ExcelPlatform.SUPERGRAFX: ["nec supergraphx hucard"],
        ExcelPlatform.SYMBIAN: ["symbian os soft."],
        ExcelPlatform.TI_99_4A: [
            "atari 800/c64/trs-80/ti99 cass.",
            "trs-80/ti-99/timex cass.",
            "texas instrument ti-99/4a cart+cass.",
            "texas instrument ti-99/4a cart.",
            "texas instrument ti-99/4a cass.",
            "texas instrument ti-99/4a disk",
            "texas instrument ti-99/4a type-in",
        ],
        ExcelPlatform.TIMETOP_GAMEKING: ["timetop game king cart."],
        ExcelPlatform.TIMETOP_GAMEKING_III: ["timetop game king 3 cart."],
        ExcelPlatform.TRS_80_COLOR_COMPUTER: [
            "apple ii/pet/trs-80 disk",
            "apple ii/trs-80 disk",
            "atari 800/apple ii/pet/trs-80 cass.",
            "atari 800/apple ii/trs-80 cass.",
            "atari 800/c64/pet/trs-80 cass.",
            "atari 800/c64/trs-80 cass.",
            "atari 800/c64/trs-80/ti99 cass.",
            "atari 800/c64/trs-80/vic-20 cass.",
            "atari 800/pet/trs-80/vic-20 cass.",
            "atari 800/trs-80 cass.",
            "atari 800/trs-80 disk",
            "atari 800/trs-80/coco cass.",
            "commodore c64/trs-80 cass.",
            "commodore c64/trs-80 disk",
            "trs-80/coco cass.",
            "trs-80/ti-99/timex cass.",
            "trs-80 cmd file",
            "trs-80 coco cart.",
            "trs-80 coco cass.",
            "trs-80 coco disk",
            "trs-80 mc-10 cass.",
            "trs-80 mod.ii 8in. disk",
            "trs-80 model 100 option rom",
            "trs-80 cass.",
            "trs-80 disk",
            "trs-80 type-in",
        ],
        ExcelPlatform.TURBOGRAFX_16: [
            "nec pc-engine hucard",
            "nec turbografx-16 cart.",
        ],
        ExcelPlatform.TURBOGRAFX_CD: [
            "nec pc-engine arcade cd",
            "nec pc-engine cd",
            "nec turbografx-cd",
        ],
        ExcelPlatform.TVOS: ["apple tvos pack."],
        ExcelPlatform.VECTREX: ["gce vectrex"],
        ExcelPlatform.VIRTUAL_BOY: ["nintendo virtual boy cart."],
        ExcelPlatform.WATARA_SUPERVISION: ["watara supervision game"],
        ExcelPlatform.WONDERSWAN: ["bandai wonderswan cart."],
        ExcelPlatform.WONDERSWAN_COLOR: ["bandai wonderswan color cart."],
        ExcelPlatform.XBOX: ["microsoft xbox dvd-rom"],
        ExcelPlatform.XBOX_360: ["microsoft xbox 360 dvd-rom"],
        ExcelPlatform.XBOX_ONE: [
            "microsoft xbox one blu-ray",
            "microsoft xbox one pack.",
        ],
        ExcelPlatform.XBOX_SERIES_X_S: ["microsoft xbox series s pack."],
        ExcelPlatform.ZX_SPECTRUM: [
            "acorn bbc/zx spectrum cass.",
            "amstrad cpc/zx spectrum cass.",
            "amstrad cpc/zx spectrum disk",
            "commodore c64/zx cass.",
            "commodore vic-20/zx cass.",
            "sinclair zx spectrum beta disk",
            "sinclair zx spectrum mgt disciple+d disk",
            "sinclair zx spectrum microdrive cart.",
            "sinclair zx spectrum microdrive cass.",
            "sinclair zx spectrum opus discovery disk",
            "sinclair zx spectrum wafadrive",
            "sinclair zx spectrum cart.",
            "sinclair zx spectrum cass.",
            "sinclair zx spectrum pack.",
            "sinclair zx spectrum type-in",
            "sinclair zx spectrum vinyl",
            "sinclair zx spectrum+3 disk",
            "sinclair zx-80 cass.",
            "sinclair zx-80 type-in",
            "sinclair zx-81 cass.",
            "sinclair zx-81 type-in",
            "sinclair zx-81 vinyl",
            "timex sinclair 2068/zx spectrum cass.",
            "zx81/spectrum/oric/atmos/laser 200/to7 cass.",
        ],
    }

    def __init__(self, validator: MatchValidator = None, config: Config = None):
        super().__init__(
            validator or MatchValidator(),
            config or Config.create(),
            spoof_headers=True,
            base_url="https://www.arcade-history.com",
        )

    async def search(self, title: str, page: int = 1, list_types: str = "") -> Any:
        return await self.get(
            f"{self.base_url}/index.php",
            params={
                "page": "database",
                "annee": "0",
                "listtypes": list_types,
                "editeur": "",
                "lemot": unidecode.unidecode(title),
                "export": "1",
                "reissue": "1",
                "pirate": "1",
                "demo": "0",
                "mamed": "1",
                "nongame": "0",
                "Tri": "0",
                "position": page,
            },
            json=False,
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.platform not in self.supported_platforms

    async def get_results_paginated(self, game: ExcelGame) -> AsyncGenerator[List[Any]]:
        page = 1
        while True:
            if game.platform == ExcelPlatform.TIMETOP_GAMEKING:
                html = await self.search("", page, "268")
            else:
                html = await self.search(game.title, page)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")

            if soup.script and f"{self.base_url}/?n=" in soup.script.get_text():
                url = soup.script.get_text().split("'")[1]
                yield [BeautifulSoup(await self.get(url, json=False), "html.parser")]
                break

            table = soup.find("div", {"id": "no-more-tables"})

            if not table:
                break

            results = table.find_all("tr", {"class": "big-box"})

            if not results:
                break

            yield results
            page += 1

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch:
        if isinstance(result, BeautifulSoup):
            _type = (
                result.find("div", {"id": "global"})
                .h2.span.get_text(strip=True)
                .lower()
            )
            name, year = (
                result.find("div", {"class": "CelluleTexte100"})
                .get_text(strip=True)
                .split("©", maxsplit=1)
            )
            name = name.strip()
            year = year.strip()[:4]  # Extract year from copyright info
            url = result.head.link["href"]
        else:
            type_elem, name_elem, year_elem, _ = result.find_all("td")

            _type = type_elem.get_text(strip=True).lower()
            name = name_elem.a["title"][6:]
            year = year_elem.get_text(strip=True)
            url = f"{self.base_url}/{name_elem.a['href']}"

        try:
            year = datetime.strptime(year, "%Y").year
        except ValueError:
            pass

        if " Demo " in name:
            return None

        match = self.validator.validate(
            game, name, release_years=[year if isinstance(year, int) else None]
        )

        match.platform_matched = _type in self.supported_platforms[game.platform]
        game_id = url.rsplit("&", maxsplit=1)[-1].split("=", maxsplit=1)[-1]

        if match.likely_match:
            return GameMatch(
                name,
                url,
                game_id,
                {
                    "title": name,
                    "platform": _type,
                    "year": year,
                    "url": url,
                },
                match,
            )

        if game.platform == ExcelPlatform.TIMETOP_GAMEKING:
            html = await self.get(f"{url}&o=9", json=False)
            soup = BeautifulSoup(html, "html.parser")

            rom_div = soup.find("div", {"class": "cartouche-milieu"}).find(
                "div", {"class": "centrer"}
            )

            for detail in rom_div.find_all("details"):
                if detail.summary:
                    mame_name = (
                        detail.summary.get_text(strip=True)
                        .split(": ", maxsplit=1)[-1]
                        .strip()
                    )

                    if mame_name:
                        match.matched = match.exact = match.platform_matched = (
                            self.validator.titles_equal_normalized(
                                game.mame_romset, mame_name
                            )
                        )

                        if match.likely_match:
                            return GameMatch(
                                name,
                                url,
                                game_id,
                                {
                                    "title": name,
                                    "platform": _type,
                                    "year": year,
                                    "url": url,
                                },
                                match,
                            )

        return None
