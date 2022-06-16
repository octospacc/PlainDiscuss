CREATE TABLE IF NOT EXISTS "Users" (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Name"	TEXT NOT NULL,
	"SecKey"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Sites" (
	"ID"	INTEGER NOT NULL UNIQUE,
	"PubKey"	TEXT NOT NULL UNIQUE,
	"SecKey"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Pages" (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Site"	INTEGER NOT NULL,
	"Path"	TEXT NOT NULL,
	PRIMARY KEY("ID" AUTOINCREMENT),
	FOREIGN KEY("Site") REFERENCES "Sites"("ID")
);

CREATE TABLE IF NOT EXISTS "Comments" (
	"ID"	INTEGER NOT NULL UNIQUE,
	"User"	INTEGER NOT NULL,
	"Page"	TEXT NOT NULL,
	"Reply"	INTEGER,
	PRIMARY KEY("ID" AUTOINCREMENT),
	FOREIGN KEY("Page") REFERENCES "Pages"("ID"),
	FOREIGN KEY("User") REFERENCES "Users"("ID")
);