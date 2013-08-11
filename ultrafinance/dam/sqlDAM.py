'''
Created on Nov 9, 2011

@author: ppa
'''
from ultrafinance.dam.baseDAM import BaseDAM
from ultrafinance.model import Quote, Tick
import sys

from sqlalchemy import Column, Integer, String, Float, Sequence, create_engine, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

import logging
LOG = logging.getLogger()

class FmSql(Base):
    __tablename__ = 'fundamental'

    id = Column(Integer, Sequence('user_id_seq'), primary_key = True)
    symbol = Column(String(12))
    field = Column(String(50))
    timeStamp = Column(String(50))
    value = Column(Float)

    def __init__(self, symbol, field, timeStamp, value):
        ''' constructor '''
        self.symbol = symbol
        self.field = field
        self.timeStamp = timeStamp
        self.value = value

    def __repr__(self):
        return "<Fundamentals('%s', '%s', '%s', '%s')>" \
           % (self.symbol, self.field, self.timeStamp, self.value)

class QuoteSql(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, Sequence('user_id_seq'), primary_key = True)
    symbol = Column(String(12))
    time = Column(Integer)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(String(12))
    adjClose = Column(String(12))

    def __init__(self, symbol, time, open, high, low, close, volume, adjClose):
        ''' constructor '''
        self.symbol = symbol
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.adjClose = adjClose

    def __repr__(self):
        return "<Quote('%s', '%s','%s', '%s', '%s','%s', '%s', '%s')>" \
           % (self.symbol, self.time, self.open, self.high, self.low, self.close, self.volume, self.adjClose)

class TickSql(Base):
    __tablename__ = 'ticks'

    id = Column(Integer, Sequence('user_id_seq'), primary_key = True)
    symbol = Column(String(12))
    time = Column(Integer)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(String(12))

    def __init__(self, symbol, time, open, high, low, close, volume):
        ''' constructor '''
        self.symbol = symbol
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self):
        return "<Tick('%s', '%s', '%s', '%s', '%s', '%s', '%s')>" \
           % (self.symbol, self.time, self.open, self.high, self.low, self.close, self.volume)

class SqlDAM(BaseDAM):
    '''
    SQL DAM
    '''
    ENGINE_DICT = {}
    SESSION_DICT = {}

    def __init__(self, echo = False):
        ''' constructor '''
        super(SqlDAM, self).__init__()
        self.echo = echo
        self.session = None
        self.first = True

    def __getEngine(self):
        ''' get engine '''
        return SqlDAM.ENGINE_DICT.get(self.db)

    def setup(self, setting):
        ''' set up '''
        if 'db' not in setting:
            raise Exception("db not specified in setting")

        self.db = setting['db']
        if self.__getEngine() is None:
            SqlDAM.ENGINE_DICT[self.db] = create_engine(self.db, echo = self.echo)
            SqlDAM.SESSION_DICT[self.db] = sessionmaker(bind = SqlDAM.ENGINE_DICT[self.db])

        self.session = SqlDAM.SESSION_DICT[self.db]()

    def __sqlToQuote(self, row):
        ''' convert row result to Quote '''
        return Quote(row.time, row.open, row.high, row.low, row.close, row.volume, row.adjClose)

    def __sqlToTick(self, row):
        ''' convert row result to Tick '''
        return Tick(row.time, row.open, row.high, row.low, row.close, row.volume)

    def __tickToSql(self, tick):
        ''' convert tick to TickSql '''
        return TickSql(self.symbol, tick.time, tick.open, tick.high, tick.low, tick.close, tick.volume)

    def __quoteToSql(self, quote):
        ''' convert tick to QuoteSql '''
        return QuoteSql(self.symbol, quote.time, quote.open, quote.high, quote.low, quote.close, quote.volume, quote.adjClose)

    def readQuotes(self, start, end):
        ''' read quotes '''
        if end is None:
            end = sys.maxint
        rows = self.session.query(QuoteSql).filter(and_(QuoteSql.symbol == self.symbol,
                                                        QuoteSql.time >= int(start),
                                                        QuoteSql.time < int(end)))

        return [self.__sqlToQuote(row) for row in rows]

    def readTicks(self, start, end):
        ''' read ticks '''
        if end is None:
            end = sys.maxint
        rows = self.session.query(TickSql).filter(and_(TickSql.symbol == self.symbol,
                                                       TickSql.time >= int(start),
                                                       TickSql.time < int(end)))

        return [self.__sqlToTick(row) for row in rows]

    def writeQuotes(self, quotes):
        ''' write quotes '''
        if self.first:
            Base.metadata.create_all(self.__getEngine(), checkfirst = True)
            self.first = False

        self.session.add_all([self.__quoteToSql(quote) for quote in quotes])

    def writeTicks(self, ticks):
        ''' write ticks '''
        if self.first:
            Base.metadata.create_all(self.__getEngine(), checkfirst = True)
            self.first = False

        self.session.add_all([self.__tickToSql(tick) for tick in ticks])

    def commit(self):
        ''' commit changes '''
        self.session.commit()

    def destruct(self):
        ''' destructor '''
        if (self.session):
            self.session.close()

    '''
    read/write fundamentals
    TODO: when doing fundamentals and quote/tick operation together,
    things may mess up
    '''
    def writeFundamental(self, keyTimeValueDict):
        ''' write fundamental '''
        if self.first:
            Base.metadata.create_all(self.__getEngine(), checkfirst = True)
            self.first = False

        sqls = self._fundamentalToSqls(keyTimeValueDict)
        self.session.add_all(sqls)

    def readFundamental(self):
        ''' read fundamental '''
        rows = self.session.query(FmSql).filter(and_(FmSql.symbol == self.symbol))
        return self._sqlToFundamental(rows)

    def _sqlToFundamental(self, rows):
        keyTimeValueDict = {}
        for row in rows:
            if row.field not in keyTimeValueDict:
                keyTimeValueDict[row.field] = {}

            keyTimeValueDict[row.field][row.timeStamp] = row.value

        return keyTimeValueDict

    def _fundamentalToSqls(self, keyTimeValueDict):
        ''' convert fundament dict to sqls '''
        sqls = []
        for key, timeValues in keyTimeValueDict.iteritems():
            for timeStamp, value in timeValues.iteritems():
                sqls.append(FmSql(self.symbol, key, timeStamp, value))

        return sqls
