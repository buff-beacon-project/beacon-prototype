import os
import sqlite3
from .types import ByteHash
from .pulse import PULSE_KEYS, pulse_to_plain_dict, pulse_from_dict, assert_next_in_chain

BEACON_DB_PATH=os.getenv('BEACON_DB_PATH', './beacon.db')
BEACON_DB_TABLE = 'beacon_records'
BEACON_DB_CERT_TABLE = 'beacon_certificates'

# convert sql row to pulse
def from_row(row):
    d = dict( zip(PULSE_KEYS, row) )

    # unserialize the anchors
    d['skipListAnchors'] = d['skipListAnchors'].split(':')

    return pulse_from_dict( d )


# convert pulse to sql row
def to_row( pulse ):
    get_pulse_val = lambda k: pulse[k].get_json_value()
    ret = list(map(get_pulse_val, PULSE_KEYS))

    n = PULSE_KEYS.index('skipListAnchors')
    # serialize the anchors
    ret[n] = ':'.join(ret[n])

    return tuple(ret)

class BeaconStore:
    def __init__(self):
        con = None
        try:
            con = self.dbConnection = sqlite3.connect(BEACON_DB_PATH)
        except Exception as e:
            if con:
                con.close()
            raise e

    def initDB(self):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS {tableName}
                (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    uri text NOT NULL,
                    version text NOT NULL,
                    cypherSuite text NOT NULL,
                    period integer NOT NULL,
                    certificateId text NOT NULL,
                    chainIndex integer NOT NULL,
                    pulseIndex integer NOT NULL,
                    timeStamp text NOT NULL,
                    localRandomValue text NOT NULL,

                    skipListLayerSize integer NOT NULL,
                    skipListNumLayers integer NOT NULL,
                    skipListAnchors text NOT NULL,
                    precommitmentValue text NOT NULL,
                    statusCode integer NOT NULL,
                    signatureValue text NOT NULL,
                    outputValue text NOT NULL
                )
            """.format(
                tableName=BEACON_DB_TABLE
            ))
            c.execute('CREATE INDEX IF NOT EXISTS {tableName}_ts ON {tableName} (timeStamp)'.format(tableName=BEACON_DB_TABLE))
            con.commit()

            c.execute("""
                CREATE TABLE IF NOT EXISTS {tableName}
                (
                    id text PRIMARY KEY,
                    certificate text NOT NULL
                )
            """.format(
                tableName=BEACON_DB_CERT_TABLE
            ))
            con.commit()

        except Exception as e:
            if con:
                con.close()
            raise e
        finally:
            c.close()

    def addCertificate(self, id, cert):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute(
                "INSERT INTO {tableName}(id, certificate) VALUES (?, ?)".format(
                    tableName = BEACON_DB_CERT_TABLE
                ),
                (id, cert)
            )
            con.commit()
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def fetchCertificateBytes(self, id):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            query = ' '.join((
                'SELECT id, certificate FROM {tableName}',
                'WHERE id = ?'
                'LIMIT 1'
            ))
            c.execute(query.format(
                tableName = BEACON_DB_CERT_TABLE
            ), (id,))
            result = c.fetchone()
            if not result:
                return None
            (id, cert) = result
            return bytes.fromhex(cert)
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def addPulse(self, pulse):
        lastPulse = self.fetchLatestPulse()
        assert_next_in_chain(lastPulse, pulse)

        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute(
                "INSERT INTO {tableName}({fields}) VALUES ({placeholders})".format(
                    tableName = BEACON_DB_TABLE,
                    fields = ', '.join(keys),
                    placeholders = ', '.join(['?'] * len(keys))
                ),
                to_row(pulse)
            )
            con.commit()
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def queryOnePulse(self, where = '', order = '', params = ()):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            query = ' '.join((
                'SELECT {fields} FROM {tableName}',
                where,
                order,
                'LIMIT 1'
            ))
            c.execute(query.format(
                tableName = BEACON_DB_TABLE,
                fields = ', '.join(keys),
            ), params)
            row = c.fetchone()
            if row == None:
                return None
            return from_row(row)
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def fetchLatestPulse(self):
        return self.queryOnePulse('ORDER BY timeStamp DESC')

    def fetchPulse(self, chain, pulse):
        return self.queryOnePulse(where='WHERE chainIndex=? AND pulseIndex=?', params=(chain, pulse))

    def fetchManyPulses(self, chain, pulseIds):
        con = self.dbConnection
        c = None
        try:
            c = con.cursor()
            keys = PULSE_KEYS
            c.execute("""
                SELECT {fields} FROM {tableName} WHERE chainIndex=? AND pulseIndex IN ({seq})
            """.format(
                tableName = BEACON_DB_TABLE,
                fields = ', '.join(keys),
                seq=','.join(['?'] * len(pulseIds))
            ), (chain,) + tuple(pulseIds))
            rows = c.fetchall()
            if len(rows) is not len(pulseIds):
                raise Exception("Could not retrieve all pulses")
            return [from_row(row) for row in rows]
        except Exception as e:
            raise e
        finally:
            if c:
                c.close()

    def fetchPulseByExactTime(self, dt):
        datestr = dt.isoformat()
        return self.queryOnePulse(where='WHERE timeStamp = ?', params=(datestr,))

    def fetchPulseByGeaterEqualTime(self, dt):
        datestr = dt.isoformat()
        return self.queryOnePulse(where='WHERE timeStamp >= ?', order='ORDER BY timeStamp ASC', params=(datestr,))

    def fetchNextPulseByTime(self, dt):
        datestr = dt.isoformat()
        return self.queryOnePulse(where='WHERE timeStamp > ?', order='ORDER BY timeStamp ASC', params=(datestr,))

    def fetchPreviousPulseByTime(self, dt):
        datestr = dt.isoformat()
        return self.queryOnePulse(where='WHERE timeStamp < ?', order='ORDER BY timeStamp DESC', params=(datestr,))
