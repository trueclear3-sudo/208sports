# 208 Pressbox — football seed data, pulled from MaxPreps 2026-10-06.
# Run: python3 data.py  -> writes data.json and checks records against MaxPreps.
import json, re, sys

MP = "https://www.maxpreps.com/id/"
# id: name, mascot, conference, maxpreps base, stated overall, stated conf
TEAMS = {
 "bla": ("Blackfoot", "Broncos", "5A High Country", MP+"blackfoot/blackfoot-broncos/football/", "3-3", "3-1"),
 "bon": ("Bonneville", "Bees", "5A High Country", MP+"idaho-falls/bonneville-bees/football/", "3-3", "2-2"),
 "cen": ("Century", "Diamondbacks", "5A High Country", MP+"pocatello/century-diamondbacks/football/", "2-4", "1-3"),
 "hig": ("Highland", "Rams", "6A High Country", MP+"pocatello/highland-rams/football/", "3-3", "0-0"),
 "hil": ("Hillcrest", "Knights", "5A High Country", MP+"idaho-falls/hillcrest-knights/football/", "6-0", "4-0"),
 "idf": ("Idaho Falls", "Tigers", "5A High Country", MP+"idaho-falls/idaho-falls-tigers/football/", "3-3", "2-2"),
 "mad": ("Madison", "Bobcats", "6A High Country", MP+"rexburg/madison-bobcats/football/", "5-1", "0-0"),
 "poc": ("Pocatello", "Thunder", "5A High Country", MP+"pocatello/pocatello-thunder/football/", "1-5", "0-4"),
 "rig": ("Rigby", "Trojans", "6A High Country", MP+"rigby/rigby-trojans/football/", "5-1", "0-0"),
 "she": ("Shelley", "Russets", "5A High Country", MP+"shelley/shelley-russets/football/", "2-4", "1-3"),
 "sky": ("Skyline", "Grizzlies", "5A High Country", MP+"idaho-falls/skyline-grizzlies/football/", "3-3", "3-1"),
 "thu": ("Thunder Ridge", "Titans", "6A High Country", MP+"idaho-falls/thunder-ridge-titans/football/", "4-2", "0-0"),
 "twi": ("Twin Falls", "Bruins", "5A Great Basin", MP+"twin-falls/twin-falls-bruins/football/", "3-3", "2-0"),
}
NAME2ID = {v[0]: k for k, v in TEAMS.items()}
# Outside opponents that count as conference games (Twin Falls' league)
OUTSIDE_CONF = {"twi": {"Canyon Ridge", "Mountain Home", "Burley", "Jerome", "Minico"}}

# date | H or A | opponent | "W 35-24" (winner score first, as MaxPreps prints) or blank if not played
SCHED = {
"idf": """8/28|H|Shelley|L 24-14
9/4|A|Teton|W 40-7
9/11|H|Thunder Ridge|L 48-13
9/18|H|Pocatello|W 35-18
9/25|A|Blackfoot|L 32-21
10/3|A|Skyline|W 28-21
10/9|H|Hillcrest|
10/16|A|Century|
10/23|A|Bonneville|""",
"sky": """8/28|A|Bonneville|W 18-14
9/4|H|Century|W 35-24
9/11|A|Pocatello|W 43-32
9/18|A|Thunder Ridge|L 30-6
9/25|H|Madison|L 21-0
10/3|H|Idaho Falls|L 28-21
10/9|A|Blackfoot|
10/16|H|Hillcrest|
10/23|H|Shelley|""",
"bon": """8/28|H|Skyline|L 18-14
9/4|A|Thunder Ridge|L 28-6
9/11|A|Burley|W 28-6
9/18|H|Blackfoot|W 21-13
9/25|A|Pocatello|W 7-6
10/2|A|Hillcrest|L 22-10
10/9|H|Century|
10/16|A|Shelley|
10/23|H|Idaho Falls|""",
"twi": """8/21|A|Sandpoint|L 36-34
8/28|A|Vallivue|L 13-8
9/4|H|Hillcrest|L 28-27
9/11|H|Blackfoot|W 34-13
9/25|A|Canyon Ridge|W 34-14
10/2|H|Mountain Home|W 52-6
10/9|A|Burley|
10/16|H|Jerome|
10/23|A|Minico|""",
"bla": """8/21|A|Shelley|W 8-7
8/28|H|Century|W 41-13
9/11|A|Twin Falls|L 34-13
9/18|A|Bonneville|L 21-13
9/25|H|Idaho Falls|W 32-21
10/2|A|Thunder Ridge|L 40-14
10/9|H|Skyline|
10/16|A|Pocatello|
10/23|H|Hillcrest|""",
"poc": """8/28|H|Hillcrest|L 32-7
9/4|A|Nampa|W 16-14
9/11|H|Skyline|L 43-32
9/18|A|Idaho Falls|L 35-18
9/25|H|Bonneville|L 7-6
10/2|A|Highland|L 17-8
10/9|A|Shelley|
10/16|H|Blackfoot|
10/23|H|Century|""",
"she": """8/21|H|Blackfoot|L 8-7
8/28|A|Idaho Falls|W 24-14
9/4|H|Sugar-Salem|L 41-0
9/11|A|Hillcrest|L 40-21
9/18|H|Canyon Ridge|W 57-21
10/2|A|Century|L 24-14
10/9|H|Pocatello|
10/16|H|Bonneville|
10/23|A|Skyline|""",
"rig": """8/21|A|Roy (UT)|W 35-0
8/28|H|Farmington (UT)|W 27-16
9/4|H|Syracuse (UT)|W 28-14
9/11|H|Minico|W 48-14
9/18|A|Box Elder (UT)|W 34-32
10/1|A|Coeur d'Alene|L 34-27
10/9|H|Thunder Ridge|
10/16|A|Highland|
10/23|H|Madison|""",
"hig": """8/21|H|Eagle|L 33-28
8/28|H|Box Elder (UT)|L 31-19
9/11|A|Capital|L 29-25
9/18|A|Lake City|W 36-0
9/25|A|Century|W 41-7
10/2|H|Pocatello|W 17-8
10/9|A|Madison|
10/16|H|Rigby|
10/23|H|Thunder Ridge|""",
"mad": """8/21|H|Minico|W 52-0
8/27|H|Riverton|W 27-0
9/4|A|Middleton|W 10-9
9/11|H|Mountain View|W 15-7
9/18|A|Owyhee|L 10-7
9/25|H|Skyline|W 21-0
10/9|H|Highland|
10/16|A|Thunder Ridge|
10/23|A|Rigby|""",
"hil": """8/28|A|Pocatello|W 32-7
9/4|A|Twin Falls|W 28-27
9/11|H|Shelley|W 40-21
9/18|A|Century|W 46-26
9/25|H|Thunder Ridge|W 52-22
10/2|H|Bonneville|W 22-10
10/9|A|Idaho Falls|
10/16|A|Skyline|
10/23|A|Blackfoot|""",
"thu": """8/27|A|Bear River (UT)|L 49-35
9/4|H|Bonneville|W 28-6
9/11|A|Idaho Falls|W 48-13
9/18|H|Skyline|W 30-6
9/25|A|Hillcrest|L 52-22
10/2|H|Blackfoot|W 40-14
10/9|A|Rigby|
10/16|H|Madison|
10/23|A|Highland|""",
"cen": """8/28|A|Blackfoot|L 41-13
9/4|A|Skyline|L 35-24
9/11|A|Canyon Ridge|W 33-16
9/18|H|Hillcrest|L 46-26
9/25|H|Highland|L 41-7
10/2|H|Shelley|W 24-14
10/9|A|Bonneville|
10/16|H|Idaho Falls|
10/23|A|Pocatello|""",
}

# number,name,positions,grade ; separated
ROSTER = {
"idf": "0,Jonathon Sereno,RB/LB,Sr;1,Jaren Hoskins,DB/OLB/WR,Sr;2,Levi Miller,RB/LB,So;3,Logan Kite,RB/OLB,Sr;4,Levi Mecham,WR/DB,Jr;5,Josh Moore,QB/DB/RB,So;6,Kenyon Spencer,RB/FS,Jr;7,Gabe Leavitt,RB/MLB,Jr;8,Everett Erickson,QB/DB/TE,Jr;9,Adree McArthur,WR/OLB,Jr;10,Ace Williams,WR/CB,Jr;11,James Richeson,WR/FS,Sr;12,Griffin Pearson,WR/DB,Sr;13,Will Thompson,QB,Sr;14,Bo Weaver,FS,Jr;15,Cooper Anderson,CB/WR,Sr;16,Johnny Pyper,TE/OLB,Sr;17,Jaxton Walker,WR/DB,Jr;18,Daniel Hillam,WR/S,Sr;19,Kona Nihipali,RB/LB,So;21,Mj Mathie,WR/SS,Jr;22,Jonah Jacobs,RB/MLB,Sr;23,Davin Wilkins,WR/DB,So;24,Jacob Mendoza,DB/RB,So;25,Chad Hoskins,CB/WR,So;26,Kade Cleary,WR/DB,So;27,Conrad Steorts,RB/S,So;28,Jack Harris,RB/MLB,Sr;30,Logan Wettenbone,RB/LB,Sr;31,Luke Peterson,TE/OLB,So;32,Layton Mitchell,WR/DB,So;33,Jagger Ferguson,WR/CB,So;35,Jake Pruitt,RB/OLB,So;36,Cooper Seefried,WR/CB,So;44,TJ Nai,RB/ILB,So;45,Grayson Jones,TE/DE,Jr;48,Kevin Woods,ILB,Jr;50,Zayden Salazar,MLB,Sr;52,Alexis Hernandez,ILB,Sr;53,Clark Fonnesbeck,T/DE,Sr;54,Jack Zundel,OL/ILB,So;55,James Jenks,T/NG,Jr;56,Easton Little,DT,Sr;57,Christopher Fernandez,OL/LB,Sr;58,Daniel Medina,OG/DE,Jr;59,Kellen McKinney,C/OLB/LS,Jr;64,Aden Murdoch,DE/OT,Sr;65,Emmanuel Landeros,OG/DE,Sr;66,Finn Gorman,OT/DE,So;67,Desmond Lopez,DE,Jr;68,Christian Montiel,G,Jr;69,Abram Jagielski,OG/DE,Jr;70,Renziel Ramirez,OL/DL,Sr;71,Ethan Jones,C,Jr;73,Read Showalter,OG/NG,So;74,Drake Wilcox,C/NG,Sr;76,Quinton Kuhn,OL/DL,Jr;77,Uziel Sanchez,OL/DL,Sr;79,Logan Gabrielsen,OL/DL,So;80,Toby Kay,TE/DE,So;84,Max Baldwin,DE/FB,Sr;87,Hudson Palmer,DE/TE,Jr;88,Boston Stevens,TE/OLB,Jr;90,Brayden Romo,DL/OL,Sr;93,Austin Green,OG/DE,Jr;98,Beau Jarvis,OG/NG,Jr;99,Landon Romero-Miranda,DE/OT,So",
"sky": "0,Cash Webster,WR,Sr;1,Taleai Molifua,WR,Sr;2,John Giannini,QB/WR,Sr;3,Sam DeMott,CB/WR,Jr;4,Fabian Vivar,K,Sr;5,Josh Meyer,SB,Jr;6,Caden Cruz,SB,Sr;7,Trevyn Phillip,FS/OLB,Jr;8,Ledger Searle,ILB/OLB,Sr;9,Ethan Elmore,DE/OLB,Sr;10,Hunter Valenzuela,DE/ATH,Fr;11,Jaxon Klein,SS/FS,Sr;12,Ernesto Molina,OLB,Sr;13,Lyncoln Holdaway,QB,So;14,Wesson Ence,QB,Fr;15,Porter Frasure,OLB/MLB,Jr;16,Cooper Landon,WR,Sr;17,Jaden Tuioti-Mariner,CB,So;18,Robby Flores,OLB,Jr;19,Joel Rose,QB/ATH,So;20,Justin Lara,CB,So;21,Jayden Cortez,CB,So;22,Wyatt Wiseman,MLB,Sr;23,Cage Lambson,CB,Sr;24,Jace Serna,RB,So;25,Kota Kluksdal,RB/OLB,So;26,Bentley Landon,CB/SS,Jr;27,Max Elmore,DB,Jr;28,Isaiah Blair,SB/CB,So;30,Ossie Watrous,CB,Jr;32,Bryan Vazquez,QB,Sr;33,J.J. Andersen,DE/DT,Jr;40,Lawson Searle,RB/ILB,Fr;43,Kyler Sargent,OLB/ATH,So;44,Riley Stewart,RB/TE,Jr;46,Kaden Mayes,LB,So;50,Rory Lancaster,DL,Sr;51,Braxton Orchard,DT/NG,Jr;52,Aidan Chavez,OL,Sr;53,Koby Koplin,T,Jr;54,Wesley Jackson,OL/DL,So;57,Austin Martin,T/G,So;60,Orlando Ramos,NG/DT,Sr;65,William Nelson,C/G,Sr;68,Wyatt Cox,G/T,Jr;71,Isidro Olivas,DL,Sr;74,Rodrigo Cortez,DL,Sr;75,Maddux McCracken,T/G,Jr;76,Matthew Sparks,C/OL,So;77,Kyron Perkins,T,Sr;78,Jaxon Brinkerhoff,G/C,Sr;80,Lincoln Raymond,WR,So;82,Raiden Brugetti,WR,Jr;85,Kolby Radford,WR/TE,So;87,Dax Clinger,WR/TE,Sr;90,Gavin Vasquez,DL,Jr;99,Preston Allen,DL,Jr",
"rig": "",
"bon": "1,Weston Ellsworth,DB/RB/WR,Sr;2,Kemper Allen,WR,Sr;3,Rydge Vail,CB/S,Sr;4,Jaxton Briggs,QB,Sr;5,Kaine Rodriguez,WR/DB,Sr;6,Carson Robinson,OLB,Sr;7,Bentley Bleazard,QB,So;8,Cooper Stephenson,HB/LB/DL,Jr;9,Carter Fontes,DE/TE,Sr;11,Sloan Harrigfeld,MLB/WR,Sr;12,Truxton Holst,LB/WR/QB,So;13,Ryan Flynn,WR/K,Sr;14,Archer Westfall,DB/SS,Sr;15,Ethan Wells,WR/QB,Jr;17,Tristan Ward,LB/RB,Jr;18,Lucas Matagi,DE/DT,Jr;21,Ryker Rainey,WR,So;22,JJ Tamayo,DB,Sr;23,Cruz Beck,HB/LB,Jr;24,Logan Arnold,DB/WR,Jr;26,Landon Sewell,HB/CB,So;28,Caden Sterling,DB/LB,Jr;30,Gage Dingman,DB,Jr;31,Ashton Clark,LB,Jr;32,Dallas Jacobsen,LB/FB,Sr;33,Spencer Blanchard,LB,Jr;34,Tayden Rapp,DB/LB,So;35,Braxton Sauer,OLB/DB,Sr;40,Kaecen Pitcher,LS/DE,Jr;42,Hank Morris,TE/DE,So;44,Wesley Matagi,NG,Fr;45,Lukah Schwarz,LB/DE,So;50,Jackson Moreau,C,Sr;51,Cooper Pugmire,DE/TE/OT,So;53,Deagan Gardner,G,Jr;54,Kade Wise,LB,So;55,Hank Averett,OL/C,So;56,Berkley Bowler,OL,So;58,Cole Campbell,OL,So;60,Kellen Felshaw,OL/DL,Jr;62,Brody Smith,OL,Jr;64,Hector Serna,OL/DL,Sr;75,James Mickelson,OL,Jr;76,Rider Petersen,DL/OL,Sr;77,Colton Young,OL,Sr;87,JT Sweet,LB/DL,So;88,Brock Ficker,TE/DE,Sr;91,Andrew Harrison,DL/DT,Sr;92,Kingston Parravano,DL,Sr;99,Saia Fonohema,DE/OLB,So",
"mad": "1,Creeden Petersen,TE,So;2,Jacob Wilkes,,Sr;3,Carter Tonks,RB/WR,So;5,Mace Mortensen,,Sr;7,Marcus Esparza,QB/WR,Sr;7,Easton Holloway,,Sr;8,Lincoln Ellsworth,,Sr;9,Hawke Cordero,,Jr;10,Micah Dougherty,QB,Jr;11,Dallas White,,Jr;11,Darren Walker,WR,So;12,Ryker Benjamin,,Jr;18,Bowen Smith,,Jr;18,Brahm Thompson,WR,Sr;19,Dawson Moffitt,C,So;21,Caydyn D. Shaw,WR/SS,Jr;22,Tyson Harding,MLB/OLB,Sr;23,Jace Johnson,,Jr;23,Bodee Grover,TE/WR,Jr;24,Landon Johnson,CB/WR,Jr;27,Grant Gugelman,,Sr;33,Knox Folsom,QB,So;33,Jansen Riding,MLB,Jr;44,Moise Joos,,Sr;47,Brenner Stoddard,K,Jr;55,Mack Richards,G/DT,Sr;67,Collins Hirschi,DE,Jr;68,Mason Cottle,T/G,Sr;68,Eli Johnson,WR/DE,Sr;70,Brock Thompson,G,Jr;77,Mark Ayala,G,Jr;99,Slate Hyde,WR,So",
"hil": "0,Boston Morris,,Sr;1,Ki Simpson,,Sr;2,J'Vion King,,Sr;3,Ethan Saunders,,Jr;6,Ameer Elabad,,Jr;8,Gavin Lamph,,Jr;9,Carl Oxborrow,,Sr;10,Maddox Ellingford,,Sr;11,Elam Miner,,Jr;12,Garrett Thompson,,Jr;13,Logan Miller,,Jr;14,Ethan Baron,,Jr;15,Cache Clements,,Jr;16,Logan Taylor,,Jr;17,Tayden Packard,,Sr;18,Licoln Giles,,Jr;19,Michael Mihu,,Jr;20,Will Morris,,Jr;21,Tristan Lewis,,Sr;22,Josh Rigby,,Jr;23,Payton Boyd,,Jr;24,Sawyer Tibbitts,,So;25,Dax Phillips,,Jr;26,Jack Cook,,Jr;28,Mario Guzman,,Jr;29,Beckett Packard,,So;31,Hayes Benson,,Sr;32,Tayson Orme,,Sr;33,Jake Stephens,,Sr;35,Qwayde Ralphs,,So;36,Mason Henrie,,So;42,Kycen Kirkham,,So;51,Tony Maw,,Sr;52,Jake Skifton,,Sr;54,Austin Snarr,,Sr;60,Kade Young,,Jr;61,Bodie Stepp,,Sr;62,Dylan Furniss,,Jr;65,Cade Sargent,,Jr;66,Tristan Zaugg,,Jr;70,Isaiah Kerbs,,Jr;72,Gavin Allen,,Sr;73,Orrin Clark,,Jr;74,Yaser Elabed,,Sr;78,Justin Furniss,,Sr",
"thu": "0,Drew Crystal,DE,Sr;1,Ryder Portmann,QB,Sr;2,Braedyn Pike,WR/FS,Jr;3,Abe Hall,QB/DB,Jr;4,Kenyan Wright,WR,Jr;5,Taylor Huseboe,DB,Sr;6,Keenan Brown,MLB/RB,Jr;7,Lane Jones,WR,Jr;8,Elliott Smith,LB,Jr;9,Kamden Hansen,ILB,Sr;10,Titan Nebeker,WR,Sr;11,Dawson Skinner,CB,Sr;12,Mason Gastelo,WR/RB,Fr;13,Kailo Malufau,DB,Sr;15,Tyce Willardson,FS/QB,So;19,Aaron Lasley,WR/K,Sr;20,Boston Martinez,DB,Jr;21,Jackson Radford,LB,Sr;22,Jakobe Christensen,RB/SS,So;23,Kendrick Azevedo,DL,Sr;25,Kayden Whyte,ILB,So;26,Beckham Porter,SS,Jr;27,Ryker Dougal,WR,So;28,Dexten Norman,CB,Jr;31,Kason Galbraith,DE,Jr;34,Tayt Nelson,RB,Jr;42,Garrett Gleave,OLB,Sr;43,Vika Malufau,DE,So;50,Owen Jones,T,Sr;51,Colby Jewett,DE,So;52,Benson Sessions,DT,Sr;55,Graham Taylor,G,Sr;56,Wyatt Bielby,OLB/MLB,Jr;57,Quincy Matos,DL,Jr;60,Hunter Hayes,DE/NG,Sr;63,Jason Olsen,DE/DT,So;66,Hunter Portmann,G,So;69,Jared West,G/DT,So;70,James Murdock,G,Sr;71,Colt Crystal,,Jr;72,Kaimen Kirkham,C,So;78,Mylez Hernandez,DE,So;81,Kooper Hansen,WR,So;83,Koleden Selanders,WR/TE,So;84,McKay Scoresby,QB/WR,Sr;85,Ethan Carlson,WR/TE,Sr;88,Caden Mennear,,Jr;89,Blake Ford,TE,So;95,Keon Cole,DT,Sr",
"bla": "0,Kaleo Brooks,DT/DE,Sr;1,Briggs Esplin,WR,Sr;2,Parker Wright,RB/DB,Sr;3,Daxtin Gallegos,FS/WR,Sr;5,Ledger Baldwin,QB,Sr;6,Mason Taylor,RB/OLB,So;7,Keaton Shoaf,WR,Sr;8,Kai Brooks,DE/DT,Sr;9,Pierce Kirwan,SB/OLB,Sr;10,Cord Williams,FS/WR,Sr;12,Kaycen Edwards,RB/DE,Sr;13,Zade Larkin,RB,Sr;14,Mason Layton,DE/WR,Sr;16,Nico Gualdron,DT,Sr;17,Rykar Wools,RB/LB,Jr;18,Austin Hurst,WR/DB,Jr;20,Gavin Blue,DB/QB,So;21,Kaeden Fisher,CB,Sr;22,German Rojo,K,Sr;24,Conner Cannon,DB,Sr;29,Teo Bautista,K,Jr;30,George Tendoy,DE/WR,Jr;38,Vinny Martinez,K,So;44,Tevita Taufui,OLB,Sr;45,Thaniel McKay,OLB/RB,Sr;50,Emmett Felton,DE/T,Sr;51,Jeremy Agundis,OL/DL,Jr;54,Jordan Alcaraz Marquez,DT/T,Jr;55,Kyler Fisher,OL,Jr;56,Zeke Mickelsen,G/MLB,Sr;58,Jacob Schrock,G/DE,Jr;65,Adam Alba,T/DT,Sr;67,Michael Sparks,C,Sr;68,Kessler Ashton,DL/OL,Sr;69,Ryan Hobley,T/G,Sr;71,Miguel Reynoso,T/DT,Sr;72,Carter Ethington,T,Sr;74,Lawrence Cousineau,T/G,Sr;77,Zak Capson,T,Jr;78,Nico Zamora,DT,Sr;83,Logan Hirschi,LB/TE,Jr;87,Hudson Burch,TE,Jr;97,Maddox Ramon,DT,Sr",
"cen": "1,Tiden Lynn,WR,Sr;3,Austin Hoyd,SS/CB,Sr;4,Teague Wheatley,,Jr;5,Brycen Lea,FS,Sr;7,Mason Erickson,DE/DL,Jr;8,Wyatt Romriell,MLB/RB,Sr;9,Jay Soto,OLB/LS,Sr;11,Tito Villano,RB,Sr;12,Justus Mangum,QB,Sr;16,Brody Jablonski,CB,Sr;19,Adrian Barber,FS/CB,Sr;21,Xenophon Fleischmann,TE/DE,Sr;24,Greyson Christensen,CB,Sr;25,Lincoln Echo Hawk,RB,Sr;41,Brycen Davis,DT,Sr;43,Leif Jackson,OLB,Sr;45,Braxton Jablonski,MLB,Sr;50,Trayson Hayes,T/G,Sr;51,Benjamin Ralphs,G,Sr;53,Isaac Giesbrecht,OLB/G,Sr;63,Aidyn Lee,T,Sr;64,Cooper Leavitt,T,Sr;66,Lincoln Corrigan,DT,Fr;71,Wrecker Havens,G,Sr;74,Wyatt Gilbert,T,Sr;75,Cole Winland,C,Jr;99,Carlos Urias,DT/DE,Sr",
"hig": "0,Easton Almond,WR,Sr;1,Cody Wallace,CB,Sr;2,Brody Jones,S,Sr;3,Cedric Mitchell,RB,Sr;4,Steele Hoopes,TE/WR,Sr;5,Lincoln Harding,CB,Jr;6,Remington Jordan,RB/WR,Jr;7,Jacob Vincent,QB,Sr;8,Anthony Millward,CB/SS,Sr;9,Jaxson Collard,DE,Sr;10,Layton Henson,TE/RB,Jr;11,Kona Baldwin,WR,Sr;12,Cooper Bringhurst,WR,Jr;13,Kellan Tingey,WR,Sr;14,Bridger Hanks,QB/K,Jr;15,Quinn Jeppesen,QB/TE,Jr;16,Daniel Parrish,OLB/MLB,Jr;17,Jax Howe,QB,So;18,Magnum Anderson,WR,Jr;19,Carter Thurman,FS/SS,Jr;20,Tristan Call,DT,Jr;21,Alex Scott,CB,Jr;22,Beckett Budge,CB,Jr;23,Landon Summers,DE,Sr;24,Benson Barlow,CB,Jr;25,Israel Morales,DE/DT,Sr;26,Ben Ditto,DE,So;27,Jaxon Buffalo,OLB,Jr;28,Malakai Mitchell,OLB,Sr;29,Ash Robertson,DE/DT,Sr;32,Jaxon Crosland,RB/WR,So;33,Brock Butler,WR,So;34,Zeadryk Alo,RB,So;36,BoDee Barnes,OLB/MLB,So;41,Jarom Michaelson,RB,Sr;43,Jaxton Andersen,OLB,So;44,Karver Kap,OLB,Jr;45,Gideon Bolin,DE/DT,Sr;46,Freedom Gonzales,MLB,Jr;52,Dallin Wilks,DE/DT,Jr;53,Mason Radford,T/C,Jr;54,Carter Dudley,G,Sr;55,Spencer Curtis,DE/DT,Jr;59,Stockton Michaelson,MLB,Jr;60,Todd Wheeler,G,Sr;62,Nolan Guerrero,C/G,Jr;65,Eli Bigelow,DT,Sr;66,Toa Laulu,G/T,So;67,Jayden Hinds,T,Sr;69,Gage Ferguson Thorne,DT,Jr;70,Tayven Scollard,T/G,Jr;71,Easton Wolfe,T/C,Jr;73,Jace Walker,G/C,Jr;77,Alex Salazar,OG,So;78,Cassidy Suapilimai,DT,Fr;79,Layton Ellsworth,G,Jr;80,Robert Wills,DE/DT,Jr;81,Brock Matthews,WR,Jr;85,Ethan Velasquez,DE,Jr;87,James Metcalf,TE/WR,So",
"poc": "1,Isaac Allen,OLB/QB,Sr;5,Jvion King,DT/RB,Sr;7,Wixom Anderson,,Sr;8,Rhev Stucki,,Jr;9,Bear Spillett,MLB/RB,Sr;12,Jakob Davis,,Sr;13,Caden Butterfield,TE,Jr;14,Kellen Walker,WR,Jr;17,Kyle Covey,FB,Sr;18,Ephriam Wadsworth,DE/TE,Sr;21,Josiah Harry,,;22,Aidan Weaver,CB,Sr;24,Cowen Gummersall,CB/WR,Sr;26,Cooper Cordell,DT/RB,So;28,Graham Farnsworth,CB/WR,Jr;30,Mak Foxx,WR,Jr;31,Gryphon Mortensen,OLB,Sr;33,Specer Kent,TE/DE,Sr;50,Talon Naasz,G/DT,Sr;54,Juan Almonte,G/DT,Sr;55,Charlie Gonzales,T,Sr;56,Ryker Baird,,Jr;60,Sam Braunersrither,C,Sr;62,Xavier Andrade,G/C,Jr;65,Cole Salce,G,Jr;67,Aaron Shreve,T,Sr;68,Hudson Hill,T/C,Jr;75,Chico King,G/DT,Jr;75,Sio Sio,DT/T,Jr",
"she": "0,Kyrev Hawker,WR/DB,Sr;1,McCoy Remington,QB/DB,Jr;2,Alex Beck,QB/DB,Sr;3,Logan Almond,WR/DB,Jr;6,Aiden Carlson,RB/LB,Sr;8,Kolson Bishop,WR/DB,Sr;9,Jade Barbo,OL/DL,Sr;10,Tryson Gundersen,WR/DB,Sr;11,Cooper Pascoe,RB/DB,So;15,Nick Fielding,RB/LB,Jr;17,Graham Webb,RB/LB,So;18,Crew Taylor,TE/LB,Jr;21,Jasen Blakely,RB/LB,Sr;22,Isaac Albright,RB/LB,Jr;23,Daxton Jones,WR/DB,Jr;24,Mason Woolf,RB/LB,So;28,Lincon Balmforth,RB/LB,So;30,Logan Balmforth,TE/LB,Jr;33,Ryker Balmforth,RB/DB,Jr;36,Briggs Beck,QB/DB/WR,So;38,Braxton Gundersen,TE/DL,So;44,Foster Searle,RB/LB,So;51,Conlan Tincher,OL/DL,So;52/25,Crosby Winder,TE/OL/LB,So;53,Linkin Sharp,C/DL,Jr;55,Alex Gotch,G/LB,Sr;59/72,Kruger Hinckley,OL/DL,So;62,Porter Mabey,OL/DL,Sr;63,Nicolas Huerta,C/DT,Sr;66/86,Kyler Cox,OL/DL/TE,Sr;69,Alex Fackrell,C/DL,Sr;70,Chase Hartley,OL/DL,Sr;77,Dillon Moss,OL/DL,Jr;78,Jackson Chandler,OL/DL,Jr;80,Rylen Gneiting,TE/DL/LS,Sr;85,Paxton Yanez,K,So;95,Brody Yanez,K,Sr",
"twi": "1,Draikyn Ferreira,,Sr;2,Ashton Hunt-Pyeatt,WR/S,Sr;3,Mason Salazar,MLB,Jr;4,Evan Debie,DL/WR,Sr;5,Ethan Hubsmith,,Sr;6,Reggie Farrer,,Sr;7,Andryk Reynolds,,So;8,Kamden Richter,WR/MLB,So;9,Jeremy Saldana,CB,Jr;10,William Poznykov,FS/CB,Sr;11,Zander Paslay,OLB,Sr;12,Bryce Nielsen,WR/TE,Sr;13,Crew Neilsen,,So;14,Atticus Swensen,,So;15,Isaac Brecht,,So;16,Jackson Sattelberg,RB,Sr;17,Bentley Hunt-Pyeatt,,So;18,Tristyn Orr,,So;20,Dax Payne,,Sr;21,Tristen Ellis,,Jr;22,Ty Fullmer,WR/C,Sr;23,Sam Swensen,,So;24,Brody Solosabal,,So;25,Beaux McPherson,WR,Sr;26,Gregory Lee,OLB,Jr;27,Dastin Wood,QB,So;28,DeAndre Rodriguez,DB/WR,So;29,Thomas Peralta,FS/WR,Sr;30,Samuel Patterson,DB/WR,So;31,Dustin Russel,,Jr;33,Carter Wills,ILB/TE,So;34,Sawyer Hartman,TE/ILB,Jr;35,Dakota Means,ILB/TE,So;37,Zack Settle,,So;38,Doria Bayanii,DB/WR,So;40,Xander Robbins,,So;42,Connor Rupp,DE,Jr;45,Caleb Fuller,,So;52,Kace Dille,,Sr;55,Kira Ifenuk,,Sr;57,Jonas Bollwinkel,,Jr;58,Ian Stallones,OL,Jr;59,Zack Subia,OL,So;60,Matt Richey,OL,So;61,Levi Niska,G,Jr;62,Aidan France,OL/DL,So;66,Frank Patterson,,Jr;67,Kayden Clopton,,Sr;68,Cooper Larsen,,;69,Marc Bolanos,OL/DL,So;70,Kobi Budden,T,Sr;71,Edwin Grove,OL,Jr;72,Miles Ware,,Sr;73,Nash Robinson,OL,So;75,Jacob Gleckler,OL,So;77,Dyer Kelsey,,So;80,Ethan Anderson,DB/WR,So;88,Connor Stevenson,WR/CB,So;97,Jayden Clopton,,Sr",
}

# Stat leaders as shown on each team's MaxPreps stats page. category: name=value, ...
# Categories: RUSH (rush yds/game) REC (rec yds/game) TD (total TDs) PTD (passing TDs) TKL (tackles/game) SACK INT
STATS = {
"hil": "REC:Ethan Saunders=75.2,Gavin Lamph=70.7,Kycen Kirkham=14.0|RUSH:Elam Miner=82.5,J'Vion King=37.7,Logan Taylor=26.7|TD:Elam Miner=6,Gavin Lamph=5,Ethan Saunders=5|TKL:J'Vion King=11.0,Maddox Ellingford=7.2,Boston Morris=5.5|SACK:Boston Morris=6.0,Tristan Zaugg=1.5,Cache Clements=1.5|INT:Ethan Saunders=2,Ki Simpson=1,J'Vion King=1|PTD:Logan Taylor=15",
"idf": "REC:Griffin Pearson=57.7,James Richeson=40.3,Daniel Hillam=32.5|RUSH:Will Thompson=48.3,Jonathon Sereno=48.2,Jack Harris=16.0|TD:Will Thompson=9,Jonathon Sereno=4,Johnny Pyper=2|TKL:Gabe Leavitt=5.8,Johnny Pyper=5.2,Adree McArthur=4.8|SACK:Max Baldwin=1.5,Johnny Pyper=1.5,Jaren Hoskins=1.0|INT:Gabe Leavitt=2,Daniel Hillam=2,Cooper Anderson=1|PTD:Will Thompson=6",
"sky": "REC:Caden Cruz=46.2,Cash Webster=33.3,Taleai Molifua=27.0|RUSH:Caden Cruz=62.8,John Giannini=37.5,Riley Stewart=33.5|TD:John Giannini=4,Riley Stewart=3,Caden Cruz=3|TKL:Ernesto Molina=10.2,Trevyn Phillip=9.3,J.J. Andersen=8.5|SACK:J.J. Andersen=4.0,Hunter Valenzuela=2.0,Ethan Elmore=2.0|INT:Jaxon Klein=2,Trevyn Phillip=1|PTD:John Giannini=6",
"rig": "",
"mad": "",
"bon": "REC:Kaine Rodriguez=65.0,Ryan Flynn=58.0,Kemper Allen=44.8|RUSH:Cooper Stephenson=136.4,Jaxton Briggs=38.2,Cruz Beck=26.0|TD:Cooper Stephenson=3,Kemper Allen=2,Ryan Flynn=2|TKL:Dallas Jacobsen=9.2,JJ Tamayo=8.0,Rydge Vail=7.8|SACK:Carter Fontes=4.0,Lucas Matagi=1.5,Sloan Harrigfeld=1.0|INT:Weston Ellsworth=2,Logan Arnold=2,Rydge Vail=1|PTD:Jaxton Briggs=6",
"thu": "REC:Titan Nebeker=69.5,McKay Scoresby=50.7,Braedyn Pike=33.2|RUSH:Tayt Nelson=77.0,Ryder Portmann=47.0,Mason Gastelo=17.2|TD:McKay Scoresby=8,Ryder Portmann=7,Titan Nebeker=6|TKL:Jackson Radford=8.7,Quincy Matos=6.3,Elliott Smith=6.0|SACK:Drew Crystal=2.0,McKay Scoresby=2.0,Keon Cole=2.0|INT:Jackson Radford=1,Abe Hall=1,McKay Scoresby=1|PTD:Ryder Portmann=16,Abe Hall=1",
"bla": "REC:Briggs Esplin=58.3,Keaton Shoaf=22.3,Mason Layton=14.5|RUSH:Parker Wright=96.8,Rykar Wools=60.0,Mason Taylor=42.8|TD:Briggs Esplin=7,Parker Wright=2,Rykar Wools=1|TKL:Tevita Taufui=5.3,Kaycen Edwards=5.3,Zeke Mickelsen=4.7|SACK:Kaleo Brooks=1.0,Rykar Wools=1.0,Zeke Mickelsen=1.0|INT:Tevita Taufui=1,Keaton Shoaf=1,Daxtin Gallegos=1|PTD:Parker Wright=5,Ledger Baldwin=2",
"cen": "REC:Tito Villano=62.7,Xenophon Fleischmann=28.7,Justus Mangum=10.0|RUSH:Tiden Lynn=53.0,Justus Mangum=45.0,Tito Villano=30.3|INT:Carlos Urias=1|PTD:Justus Mangum=2",
"hig": "REC:Kona Baldwin=56.8,Easton Almond=43.7,Cedric Mitchell=40.3|RUSH:Cedric Mitchell=90.7,Quinn Jeppesen=29.6,Easton Almond=17.5|TD:Cedric Mitchell=10,Kellan Tingey=5,Easton Almond=4|TKL:Malakai Mitchell=9.0,Karver Kap=9.0,Stockton Michaelson=8.8|SACK:Jaxson Collard=2.0,Landon Summers=1.5,Dallin Wilks=0.5|INT:Carter Thurman=2|PTD:Jacob Vincent=10",
"poc": "REC:Isaac Allen=31.7,Ephriam Wadsworth=25.7,Cowen Gummersall=21.3|RUSH:Graham Farnsworth=11.7,Rhev Stucki=5.7,Bear Spillett=1.7|INT:Cowen Gummersall=2,Ephriam Wadsworth=1|PTD:Rhev Stucki=3",
"she": "REC:Kyrev Hawker=23.8,Aiden Carlson=2.4,Cooper Pascoe=2.3|RUSH:Kyrev Hawker=72.0,Isaac Albright=37.8,Ryker Balmforth=28.4|TD:Alex Beck=5,Kyrev Hawker=4,Ryker Balmforth=2|TKL:Ryker Balmforth=6.6,Isaac Albright=6.0,Jasen Blakely=5.7|SACK:Alex Fackrell=1.0,Alex Gotch=1.0|INT:Jasen Blakely=1,McCoy Remington=1,Aiden Carlson=1|PTD:Alex Beck=1",
"twi": "REC:Bryce Nielsen=48.7,Draikyn Ferreira=42.3,Jackson Sattelberg=12.7|RUSH:Jackson Sattelberg=90.5,Ethan Hubsmith=16.5,Tristen Ellis=14.7|TD:Jackson Sattelberg=11,Bryce Nielsen=5,Draikyn Ferreira=4|TKL:Kace Dille=12.0,Kamden Richter=11.5,Reggie Farrer=10.5|SACK:Kamden Richter=4.0,Connor Rupp=2.0,Reggie Farrer=1.0|INT:Kamden Richter=1,Ty Fullmer=1,Kace Dille=1|PTD:Ethan Hubsmith=9,Bryce Nielsen=1",
}

# ---------- JV and Freshman (pulled 2026-10-06). Result = "W 28-26 (OT)" or a kickoff time or blank ----------
LOWER = {"jv": {
"bla": "8/22|H|Skyline|W 28-26 (OT)\n8/22|H|Shelley|W 2-0 (FF)\n8/27|A|Century|L 21-14\n9/10|H|Twin Falls|W 45-0\n9/19|H|Bonneville|W 41-20\n9/24|A|Idaho Falls|W 49-18\n10/1|H|Thunder Ridge|L 30-21\n10/7|A|Skyline|7:00pm\n10/15|H|Pocatello|7:00pm\n10/21|A|Hillcrest|7:00pm",
"bon": "8/22|A|Ririe|W 40-6\n8/27|A|Skyline|L 32-22\n9/3|H|Thunder Ridge|L 27-12\n9/10|H|Hillcrest|W 17-15\n9/19|A|Blackfoot|L 41-20\n9/24|H|Pocatello|W 47-13\n10/1|H|Hillcrest|L 42-29\n10/8|H|Century|6:30pm\n10/15|H|Shelley|7:00pm\n10/22|A|Idaho Falls|7:00pm",
"cen": "8/27|H|Blackfoot|W 21-14\n9/3|H|Skyline|L 38-21\n9/10|H|Canyon Ridge|W 12-6\n9/17|A|Hillcrest|6:30pm\n9/24|A|Highland|6:30pm\n10/1|A|Sugar-Salem|L 34-0\n10/8|A|Bonneville|6:30pm\n10/22|H|Pocatello|7:00pm",
"hig": "8/27|A|Box Elder (UT)|6:00pm\n9/3|A|Eagle|W 37-16\n9/10|H|Capital|L 55-52 (4OT)\n9/16|H|Twin Falls|7:00pm\n9/24|H|Century|6:30pm\n10/1|H|Pocatello|7:00pm\n10/7|H|Madison|7:00pm\n10/15|A|Rigby|7:00pm\n10/22|A|Thunder Ridge|7:00pm",
"hil": "8/27|H|Pocatello|W 39-6\n9/10|A|Bonneville|L 17-15\n9/17|H|Century|6:30pm\n9/24|H|Thunder Ridge|L 33-16\n10/1|A|Bonneville|W 42-29\n10/15|H|Skyline|7:00pm\n10/21|H|Blackfoot|7:00pm",
"idf": "9/3|A|Sugar-Salem|L 52-20\n9/10|H|Thunder Ridge|L 53-6\n9/17|H|Pocatello|7:00pm\n9/24|H|Blackfoot|L 49-18\n10/22|H|Bonneville|7:00pm",
"mad": "8/21|H|Minico|L 36-8\n9/4|H|Middleton|L 35-8\n9/10|H|Mountain View|L 31-6\n9/18|H|Owyhee|L 20-18\n9/24|H|Skyline|W 30-14\n10/7|A|Highland|7:00pm\n10/15|H|Thunder Ridge|7:00pm\n10/22|H|Rigby|7:00pm",
"poc": "8/27|A|Hillcrest|L 39-6\n9/4|H|Nampa|4:00pm\n9/10|A|Skyline|W 40-0\n9/17|A|Idaho Falls|7:00pm\n9/24|A|Bonneville|L 47-13\n10/1|A|Highland|7:00pm\n10/8|H|Shelley|7:00pm\n10/15|A|Blackfoot|7:00pm\n10/22|A|Century|7:00pm",
"rig": "8/21|A|Roy (UT)|W 56-6\n8/27|A|Cedar Valley|W 42-14\n9/3|H|Syracuse (UT)|W 42-3\n9/10|A|Minico|W 27-20\n9/17|H|Box Elder (UT)|L 21-20\n9/24|H|Star Valley|W 28-14\n10/2|H|Coeur d'Alene|W 40-0\n10/8|H|Thunder Ridge|7:00pm\n10/15|H|Highland|7:00pm\n10/22|A|Madison|7:00pm",
"she": "8/22|A|Blackfoot|L 2-0 (FF)\n9/17|A|Canyon Ridge|W 34-14\n10/8|A|Pocatello|7:00pm\n10/15|A|Bonneville|7:00pm",
"sky": "8/22|A|Blackfoot|L 28-26 (OT)\n8/27|H|Bonneville|W 32-22\n9/3|A|Century|W 38-21\n9/10|H|Pocatello|L 40-0\n9/17|H|Thunder Ridge|L 14-6\n9/24|A|Madison|L 30-14\n10/7|H|Blackfoot|7:00pm\n10/15|A|Hillcrest|7:00pm",
"thu": "8/26|A|Bear River (UT)|W 40-26\n9/3|A|Bonneville|W 27-12\n9/10|A|Idaho Falls|W 53-6\n9/17|A|Skyline|W 14-6\n9/24|A|Hillcrest|W 33-16\n10/1|A|Blackfoot|W 30-21\n10/8|A|Rigby|7:00pm\n10/15|A|Madison|7:00pm\n10/22|H|Highland|7:00pm",
"twi": "8/27|H|Vallivue|W 28-12\n9/10|A|Blackfoot|L 45-0\n9/16|A|Highland|7:00pm\n9/24|A|Sugar-Salem|L 47-25\n10/1|A|Mountain Home|6:00pm\n10/8|A|Burley|6:30pm",
}, "fr": {
"bla": "8/22|H|Shelley|L 28-12\n8/27|A|Century|W 22-6\n9/10|H|Twin Falls|L 34-18\n9/17|H|Bonneville|L 20-0\n9/24|A|Idaho Falls|W 14-6\n10/1|H|Thunder Ridge|L 24-6\n10/7|A|Skyline|4:30pm\n10/15|H|Pocatello|4:30pm\n10/21|A|Hillcrest|4:30pm",
"bon": "8/27|A|Skyline|W 60-18\n9/3|H|Thunder Ridge|W 40-0\n9/10|H|Burley|W 53-14\n9/17|A|Blackfoot|W 20-0\n9/24|H|Jerome|W 21-0 (FF)\n10/1|H|Hillcrest|W 46-6\n10/8|A|Century|4:30pm\n10/15|H|Shelley|4:30pm\n10/22|A|Idaho Falls|4:30pm",
"cen": "8/27|H|Blackfoot|L 22-6\n9/3|H|Skyline|L 30-12\n9/10|H|Canyon Ridge|W 12-6\n9/17|A|Hillcrest|4:00pm\n9/24|A|Highland|4:00pm\n10/1|A|Shelley|L 27-14\n10/8|H|Bonneville|4:30pm",
"hig": "8/26|A|Box Elder (UT)|6:00pm\n9/3|A|Eagle|L 42-14\n9/10|H|Capital|W 34-12\n9/16|H|Twin Falls|L 16-14\n9/24|H|Century|4:00pm\n10/1|H|Sugar-Salem|W 41-30\n10/7|H|Madison|4:30pm\n10/15|A|Rigby|4:30pm\n10/22|A|Thunder Ridge|4:30pm",
# Hillcrest freshman: corrected by David 2026-10-06 from his Hillcrest app. "!" = trust this row over the other school's page.
"hil": "8/27|A|Bishop Kelly|L 32-0|!\n9/3|H|Twin Falls|L 34-27|!\n9/10|A|Shelley|L 27-12|!\n9/17|A|Century|W 30-26|!\n9/26|A|Thunder Ridge|L 21-14|!\n10/1|A|Bonneville|L 46-6|!\n10/8|H|Idaho Falls|3:00pm|!\n10/15|H|Skyline|4:30pm|!\n10/21|H|Blackfoot|4:30pm|!",
"idf": "8/27|A|Shelley|L 28-12\n9/10|A|Thunder Ridge|L 41-0\n9/24|H|Blackfoot|L 14-6\n10/22|H|Bonneville|4:30pm",
"mad": "8/21|H|Minico|W 48-0\n9/4|A|Middleton|W 21-20\n9/10|A|Mountain View|L 41-23\n9/17|A|Owyhee|W 39-14\n9/24|H|Skyline|W 59-13\n10/7|A|Highland|4:30pm\n10/15|H|Thunder Ridge|4:30pm\n10/22|H|Rigby|4:30pm",
"poc": "10/8|H|Shelley|4:30pm\n10/15|A|Blackfoot|4:30pm",
"rig": "8/21|A|Roy (UT)|W 55-6\n9/3|A|Rocky Mountain|W 56-27\n9/10|A|Minico|W 49-6\n9/17|H|Box Elder (UT)|L 31-21\n10/2|H|Coeur d'Alene|W 61-24\n10/8|H|Thunder Ridge|4:30pm\n10/15|H|Highland|\n10/22|A|Madison|",
"she": "8/22|A|Blackfoot|W 28-12\n8/27|H|Idaho Falls|W 28-12\n9/3|A|Sugar-Salem|L 40-6\n9/10|H|Hillcrest|W 27-12\n9/17|A|Canyon Ridge|W 34-13\n10/1|H|Century|W 27-14\n10/8|A|Pocatello|4:30pm\n10/15|A|Bonneville|4:30pm\n10/22|H|Skyline|4:30pm",
"sky": "8/27|H|Bonneville|L 60-18\n9/3|A|Century|W 30-12\n9/9|A|Kimberly|L 30-12\n9/17|H|Thunder Ridge|L 28-6\n9/24|A|Madison|L 59-13\n10/7|H|Blackfoot|4:30pm\n10/15|A|Hillcrest|4:30pm\n10/22|A|Shelley|4:30pm",
"thu": "8/26|A|Bear River (UT)|L 27-0\n9/3|A|Bonneville|L 40-0\n9/10|H|Idaho Falls|W 41-0\n9/17|A|Skyline|W 28-6\n9/24|A|Hillcrest|W 21-14\n10/1|A|Blackfoot|W 24-6\n10/8|A|Rigby|4:30pm\n10/15|A|Madison|4:30pm\n10/22|H|Highland|4:30pm",
"twi": "8/27|H|Vallivue|W 46-6\n9/10|A|Blackfoot|W 34-18\n9/16|A|Highland|W 16-14\n9/24|A|Canyon Ridge|W 33-8\n10/1|A|Kimberly|W 32-24\n10/8|A|Burley|3:30pm",
}}
STATED = {"jv": dict(bla="5-2",bon="3-4",cen="2-2",hig="1-1",hil="2-2",idf="0-3",mad="1-4",poc="1-2",rig="6-1",she="1-1",sky="2-4",thu="6-0",twi="1-2"),
          "fr": dict(bla="2-4",bon="6-0",cen="1-3",hig="2-2",hil="1-5",idf="0-3",mad="4-1",poc="0-0",rig="4-1",she="5-1",sky="1-4",thu="4-2",twi="5-0")}
# Hillcrest freshman roster, from the printed team sheet David photographed 2026-10-06 (last four have no number)
HIL_FR = "2,Elijah Zuniga;4,Weston Harris;5,Gunnar Belnap;11,Jayce Clay;12,Kasten Horn;13,Kouper Keckley;14,Anthony Patrick;15,Joey Nichols;17,Ammon Wilson;19,Jace Trane;21,Jordan Henry;22,Grant Carr;27,Mitchell Skifton;29,Kaden Tarbet;31,Luke Powell;32,Mason Witte;33,Luke Simpson;35,Jakob Vollmer;40,Easton Howell;44,Stockton Sessions;55,Bo Bojorquez;58,Dax Draper;59,Kycen Jackson;64,Kristopher Moore;65,Easton Floyd;68,Dominic Labra;74,Emmett Allen;75,Blake Bateman;76,Maverick Jennings;77,Owen Wardar;78,Jay Cavness;85,Nash Benson;,Ike Bowers;,Joseph Garvin;,Logan Whitaker;,Ryan Johnson"

from datetime import date
def iso(d):
    m, day = d.split("/")
    return "2026-%02d-%02d" % (int(m), int(day))
def dnum(i): return date.fromisoformat(i).toordinal()
def parse(res):
    m = re.match(r"([WLT]) (\d+)-(\d+)\s*(\(.*\))?", res or "")
    if m:
        hi, lo = int(m.group(2)), int(m.group(3))
        return ((hi, lo) if m.group(1) != "L" else (lo, hi)), (m.group(4) or "").strip("()"), None
    t = re.match(r"(\d+):(\d+)\s*(am|pm)", res or "", re.I)
    return None, "", ("%s:%s %s" % (t.group(1), t.group(2), t.group(3).upper()) if t else None)

def merge(level, sched, strict, flags):
    """Each game between two app teams is listed on both schools' pages. Pair the listings up and cross-check."""
    rows = []
    for tid, text in sched.items():
        for line in text.strip().split("\n"):
            if not line.strip(): continue
            f = [x.strip() for x in line.split("|")]
            d, ha, opp, res = f[:4]
            sc, note, tm = parse(res)
            rows.append(dict(tid=tid, date=iso(d), ha=ha, opp=opp, oid=NAME2ID.get(opp), sc=sc, note=note, tm=tm, used=False, auth=len(f) > 4))
    games, lone = [], 0
    for r in rows:
        if r["used"]: continue
        r["used"] = True
        tid, oid = r["tid"], r["oid"]
        if not oid:
            home = r["ha"] == "H"
            g = dict(home=tid if home else None, away=None if home else tid, outside=r["opp"],
                     outsideConf=r["opp"] in OUTSIDE_CONF.get(tid, ()),
                     hs=None, **{"as": None})
            if r["sc"]: g["hs"], g["as"] = (r["sc"] if home else r["sc"][::-1])
            date_, tm, note = r["date"], r["tm"], r["note"]
        else:
            tol = 0 if strict else 3
            c = sorted([x for x in rows if not x["used"] and x["tid"] == oid and x["oid"] == tid and abs(dnum(x["date"]) - dnum(r["date"])) <= tol],
                       key=lambda x: abs(dnum(x["date"]) - dnum(r["date"])))
            p = c[0] if c else None
            home, away = (tid, oid) if r["ha"] == "H" else (oid, tid)
            mine = {tid: r["sc"][0], oid: r["sc"][1]} if r["sc"] else None
            theirs = None
            g = dict(home=home, away=away)
            key = "%s %s %s-%s" % (level.upper(), r["date"], TEAMS[away][0], TEAMS[home][0])
            auth = r if r["auth"] else (p if p and p["auth"] else None)
            if p: p["used"] = True
            if auth:  # a row the owner corrected by hand wins outright
                a, b = auth["tid"], auth["oid"]
                home, away = (a, b) if auth["ha"] == "H" else (b, a)
                g = dict(home=home, away=away)
                mine = {a: auth["sc"][0], b: auth["sc"][1]} if auth["sc"] else None
                r = auth; p = None
            elif p:
                theirs = {oid: p["sc"][0], tid: p["sc"][1]} if p["sc"] else None
                if mine and theirs and mine != theirs:
                    assert not strict, ("score mismatch", key)
                    flags.append(key + ": the two schools' pages show different scores — check it")
                if p["ha"] == r["ha"]:
                    g["siteUnknown"] = True
                    if strict: flags.append(key + ": both schools list this as a home game — confirm where it was played")
            elif not auth:
                assert not strict, ("listed by one school only", key)
                lone += 1
            sc = mine or theirs
            g["hs"], g["as"] = (sc[home], sc[away]) if sc else (None, None)
            src = r if (r["sc"] or not p or not p["sc"]) else p
            date_, tm, note = src["date"], r["tm"] or (p and p["tm"]), r["note"] or (p["note"] if p else "")
        if level == "v": tm = "6:00 PM" if date_ == "2026-10-03" else "7:00 PM"
        ids = sorted(x for x in (g["home"], g["away"]) if x)
        g.update(level=level, date=date_, time=tm, note=note, sponsors=[], sponsorMode="winner")
        g["id"] = level + ":" + date_ + ":" + ":".join(ids) + (":x" if len(ids) == 1 else "")
        games.append(g)
    seen = {}
    for g in games:  # same pair can meet twice at lower levels; keep ids unique
        seen[g["id"]] = seen.get(g["id"], 0) + 1
        if seen[g["id"]] > 1: g["id"] += ":" + str(seen[g["id"]])
    return sorted(games, key=lambda g: (g["date"], g["id"])), lone

def record(games, tid):
    w = l = cw = cl = 0
    conf = TEAMS[tid][2]
    for g in games:
        if tid not in (g["home"], g["away"]) or g["hs"] is None: continue
        mine, theirs = (g["hs"], g["as"]) if g["home"] == tid else (g["as"], g["hs"])
        other = g["away"] if g["home"] == tid else g["home"]
        isconf = (TEAMS[other][2] == conf) if other else g.get("outsideConf")
        if mine > theirs: w += 1; cw += isconf
        elif mine < theirs: l += 1; cl += isconf
    return "%d-%d" % (w, l), "%d-%d" % (cw, cl)

def build():
    flags, allgames = [], []
    vg, _ = merge("v", SCHED, True, flags); allgames += vg
    for tid, t in TEAMS.items():
        calc = record(vg, tid); ok = calc == (t[4], t[5])
        print("V  %-14s %s conf %s (MaxPreps %s, %s) %s" % (t[0], calc[0], calc[1], t[4], t[5], "ok" if ok else "MISMATCH"))
        assert ok
    for lv in ("jv", "fr"):
        g, lone = merge(lv, LOWER[lv], False, flags); allgames += g
        diff = []
        for tid, t in TEAMS.items():
            calc = record(g, tid)[0]
            if calc != STATED[lv][tid]: diff.append("%s app %s vs MaxPreps %s" % (t[0], calc, STATED[lv][tid]))
        print(lv.upper(), len(g), "games,", sum(1 for x in g if x["hs"] is not None), "with scores,", lone, "listed by one school only")
        for d in diff: print("   record differs:", d)
        if diff: flags.append("%s records differ from the school's own page where the opponent posted a score the school did not: %s" % (lv.upper() if lv == "jv" else "Freshman", "; ".join(diff)))
    teams = []
    for tid, (name, mascot, conf, url, ovr, cf) in TEAMS.items():
        roster = []
        for p in filter(None, ROSTER[tid].split(";")):
            n, nm, pos, gr = p.split(",")
            roster.append(dict(n=n, name=nm, pos=pos.replace("/", ", "), gr=gr))
        fr = [dict(n=p.split(",")[0], name=p.split(",")[1], pos="", gr="Fr") for p in HIL_FR.split(";")] if tid == "hil" else []
        stats = {}
        for part in filter(None, STATS[tid].split("|")):
            cat, rest = part.split(":")
            stats[cat] = [dict(name=x.split("=")[0], v=float(x.split("=")[1])) for x in rest.split(",")]
        teams.append(dict(id=tid, name=name, mascot=mascot, conf=conf, links=dict(football=url),
                          rosters=dict(v=roster, jv=[], fr=fr), stats=stats, favBiz=[]))
    flags += ["Rigby: no varsity roster posted on MaxPreps — paste one in under Rosters",
              "Rigby: no player stats posted on MaxPreps", "Madison: no player stats posted on MaxPreps",
              "Hillcrest: MaxPreps varsity roster lists no positions",
              "Hillcrest freshman roster: Ike Bowers, Joseph Garvin, Logan Whitaker and Ryan Johnson have no jersey number on the sheet",
              "JV and Freshman: some played games have no score on MaxPreps — add them under Scores when you find them"]
    data = dict(season="2026", pulled="2026-10-06", sports=[dict(id="football", name="Football", on=True)],
                teams=teams, games=allgames, businesses=[], flags=flags)
    json.dump(data, open("data.json", "w"), separators=(",", ":"))
    print(len(allgames), "games total;", len(flags), "flags")
    for f in flags: print("  FLAG", f)

build()
