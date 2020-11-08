# mentorAPI

Mentor API server written in python3, using cherrypy as a server framework and PostgreSQL for storing contact (e-mail, social media etc.) and approximately location information about the user who wants to provide help and who provides this kind of information to the (non)authorized public by entering it into _mentorAPI_'s database by using _mentorAPI_ or one of the frontends available for it.

**For the OpenStreetMap Community** this means that I enable the experienced ones to be able to help newbies. Newbies can utilize mentorAPIs facilities to find friendly persons who want to help people getting into OpenStreetMap, who want to help cut down entry barriers for non-technos and who want to make OpenStreetMap more divers than it is already.

## Create database

Click [here](database/README.md) for a how to create the database mentorAPI needs.

## Test OAuth and mentorAPI's log in system

1. Change in the directory `database` and start a terminal there.
2. Issue `pip3 install psycopg2` to install `psycopg2`.
3. Issue the cmd `python3 setup.py` (requires a running PostgreSQL instance).
4. Change back to the root dir of this API.
5. Start mentorAPI by issueing `python3 service.py`.
6. Change to the directory `test` and start a terminal there (see also [the README file there](test/README.md)).
7. Issue `python3 -m http.server 8080` and pinpoint your browser to http://localhost:8080/index.html in order to test _mentorAPI_.

# Thank You

- @hauke96 for explaining me the security/cryptographic and oauth stuff :)
- "OSM Africa Tagging" (Telegram group) for inspiration. You might not notice but your work inspired me a lot. Exspecially the female group owner has done a great great job in inspiring me.
- OSM Hamburg for motivating me. Exspecially the non-technical female voice who initiated our discussion about the entry barriers newbies from the non-technical world might run into.
