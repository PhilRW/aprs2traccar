# About

This little Docker container will connect to [APRS-IS](http://aprs-is.net/) over the internet and copy APRS position reports into device locations in a [Traccar](https://www.traccar.org/) server.

## How to

Clone this repo and then add this to your `docker-compose.yml` file:

```yaml
  aprs2traccar:
    build: ./aprs2traccar  # or wherever you cloned the source code for the repo
    container_name: aprs2traccar  # optional
    environment:
      - "CALLSIGN=FO0BAR"
      - "APRS_HOST=noam.aprs2.net"  # optional but recommended, defaults to rotate.aprs.net
      - "APRS_FILTER=b/FO0BAR*"  # optional, defaults to b/CALLSIGN
      - "TRACCAR_HOST=https://traccar.example.com"  # optional, defaults to http://traccar:8082
      - "LOG_LEVEL=DEBUG"  # optional, defaults to INFO
    restart: unless-stopped
  ```
  
  * `CALLSIGN` is your callsign and what you use to connect to APRS-IS.
  * `APRS_HOST` is the APRS-IS host to connect to.
  * `APRS_FILTER` is the [filter](http://aprs-is.net/javAPRSFilter.aspx) for stations to track and send to Traccar.
  * `TRACCAR_HOST` is your Traccar server's URI/URL. If run in the same docker-compose stack, name your Traccar service `traccar` and omit this env var.

> NOTE: You will want to create devices for each Callsign you intend to track in Traccar, it will not create them automatically for you.
