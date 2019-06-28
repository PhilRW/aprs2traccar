import logging
import os
import threading

import aprslib
import geopy.distance
import requests

ATTR_ACCURACY = 'accuracy'
ATTR_ALTITUDE = 'altitude'
ATTR_COMMENT = 'comment'
ATTR_COURSE = 'course'
ATTR_FORMAT = 'format'
ATTR_FROM = 'from'
ATTR_ID = 'id'
ATTR_LATITUDE = 'lat'
ATTR_LONGITUDE = 'lon'
ATTR_POS_AMBIGUITY = 'posambiguity'
ATTR_SPEED = 'speed'
DEFAULT_APRS_HOST = 'rotate.aprs.net'
DEFAULT_APRS_PASSWORD = '-1'
DEFAULT_TRACCAR_HOST = 'http://traccar:8082'
FILTER_PORT = 14580
MSG_FORMATS = ['compressed', 'uncompressed', 'mic-e']

LOGGER = logging.getLogger(__name__)


def gps_accuracy(gps, posambiguity: int) -> int:
    """Calculate the GPS accuracy based on APRS posambiguity."""

    pos_a_map = {0: 0,
                 1: 1 / 600,
                 2: 1 / 60,
                 3: 1 / 6,
                 4: 1}
    if posambiguity in pos_a_map:
        degrees = pos_a_map[posambiguity]

        gps2 = (gps[0], gps[1] + degrees)
        dist_m = geopy.distance.distance(gps, gps2).m

        accuracy = round(dist_m)
    else:
        message = "APRS position ambiguity must be 0-4, not '{0}'.".format(
            posambiguity)
        raise ValueError(message)

    return accuracy


class AprsListenerThread(threading.Thread):
    """APRS message listener."""

    def __init__(self, callsign: str,
            aprs_host: str,
            aprs_server_filter: str,
            traccar_host: str,
            aprs_password: str = DEFAULT_APRS_PASSWORD):
        """Initialize the class."""
        super().__init__()

        self.callsign = callsign
        self.aprs_server_filter = aprs_server_filter
        self.traccar_host = traccar_host

        self.ais = aprslib.IS(self.callsign, passwd=aprs_password, host=aprs_host, port=FILTER_PORT)

    def run(self):
        """Connect to APRS and listen for data."""
        self.ais.set_filter(self.aprs_server_filter)

        try:
            LOGGER.info(f"Opening connection to APRS with callsign {self.callsign}.")
            self.ais.connect()
            self.ais.consumer(callback=self.rx_msg, immortal=True)
        except OSError:
            LOGGER.info(f"Closing connection to APRS with callsign {self.callsign}.")

    def stop(self):
        """Close the connection to the APRS network."""
        self.ais.close()

    def tx_to_traccar(self, query: str):
        """Send position report to Traccar server"""
        LOGGER.debug(f"tx_to_traccar({query})")
        url = f"{self.traccar_host}/?{query}"
        try:
            post = requests.post(url)
            logging.debug(f"POST {post.status_code} {post.reason} - {post.content.decode()}")
            if post.status_code == 400:
                logging.warning(
                    f"{post.status_code}: {post.reason}. Please create device with matching identifier on Traccar server.")
            elif post.status_code > 299:
                logging.error(f"{post.status_code} {post.reason} - {post.content.decode()}")
        except OSError:
            logging.exception(f"Error sending to {url}")

    def rx_msg(self, msg: dict):
        """Receive message and process if position."""
        LOGGER.debug("APRS message received: %s", str(msg))
        if msg[ATTR_FORMAT] in MSG_FORMATS:
            dev_id = msg[ATTR_FROM]
            lat = msg[ATTR_LATITUDE]
            lon = msg[ATTR_LONGITUDE]

            query_string = f"{ATTR_ID}={dev_id}&{ATTR_LATITUDE}={lat}&{ATTR_LONGITUDE}={lon}"

            if ATTR_POS_AMBIGUITY in msg:
                pos_amb = msg[ATTR_POS_AMBIGUITY]
                try:
                    query_string += f"&{ATTR_ACCURACY}={gps_accuracy((lat, lon), pos_amb)}"
                except ValueError:
                    LOGGER.warning(f"APRS message contained invalid posambiguity: {pos_amb}")
            for attr in [ATTR_ALTITUDE,
                         ATTR_SPEED]:
                if attr in msg:
                    query_string += f"&{attr}={msg[attr]}"

            self.tx_to_traccar(query_string)


if __name__ == '__main__':
    log_level = os.environ.get("LOG_LEVEL", "INFO")

    logging.basicConfig(level=log_level)

    callsign = os.environ.get("CALLSIGN")
    aprs_host = os.environ.get("APRS_HOST", DEFAULT_APRS_HOST)
    filter = os.environ.get("APRS_FILTER", f"b/{callsign}")
    password = os.environ.get("APRS_PASSWORD", DEFAULT_APRS_PASSWORD)
    traccar_host = os.environ.get("TRACCAR_HOST", DEFAULT_TRACCAR_HOST)

    if not callsign:
        logging.fatal("Please provide your callsign to login to the APRS server.")
        exit(1)

    ALT = AprsListenerThread(callsign, aprs_host, filter, traccar_host, password)
    ALT.start()
