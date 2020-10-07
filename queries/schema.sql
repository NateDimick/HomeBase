CREATE TABLE Scores (
    gameid INTEGER PRIMARY KEY,
    hometeam TEXT,
    awayteam TEXT,
    homescore INTEGER,
    awayscore INTEGER
);

CREATE TABLE Games (
    gameid INTEGER PRIMARY KEY,
    week INTEGER,
    season INTEGER,
    booktotal REAL
);