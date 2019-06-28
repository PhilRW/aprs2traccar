Add this to your `docker-compose.yml` file:

```yaml
  aprs2traccar:
    image: philrw/aprs2traccar
    container_name: aprs2traccar
    environment:
      - CALLSIGN=FO0BAR
      - APRS_HOST=noam.aprs2.net # optional, defaults to rotate.aprs.net
      - APRS_FIlTER=b/FO0BAR*  # optional, defaults to b/CALLSIGN
      - TRACCAR_HOST=https://traccar.example.com  # optional, defaults to http://traccar:8082
    restart: unless-stopped
  ```