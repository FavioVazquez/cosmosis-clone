from .output_base import OutputBase
from . import utils
import numpy as np
import os
from collections import OrderedDict
import sqlite3
import datetime

TIME_FORMAT="%Y_%m_%d_%H_%M_%S"
TIME_FORMAT_EXAMPLE = datetime.datetime.now().strftime(TIME_FORMAT)

class SqliteOutput(OutputBase):
    FILE_EXTENSION = ".sq3"
    _aliases = ["sqlite", "sqlite3", "db"]

    def __init__(self, filename, tag, sampler, ini, rank=0, nchain=1):
        super(SqliteOutput, self).__init__()

        self._db = sqlite3.connect(filename)
        self.sampler = sampler
        self.nchain = nchain
        self.master = (rank==0)
        self.inifile_name = ini
        self.tag = tag
        self.timestamp = datetime.datetime.now().strftime(TIME_FORMAT)
        self._name = "{0}_{1}_{2}_{3}".format(tag, rank+1, nchain, self.timestamp)
        if self.master:
            self.setup_db_file()
        #also used to store comments:
        self._table_name = self._name+"_chain"
        self._metadata_name = self._name+"_meta"

        self._metadata = OrderedDict()
        self._comments = []
        self._params = []
        self._final_metadata = OrderedDict()
        self.metadata("timestamp", self.timestamp)

    def setup_db_file(self):
        sql = "create table if not exists runs \
        (tag text, ini text, sampler text, date text, nchain integer, timestamp text)"
        with self._db:
            self._db.execute(sql)

    def create_tables(self):
        with self._db:

            #Create an entry for this run in the main list of tables
            if self.master:
                date_string = datetime.datetime.utcnow().isoformat()
                sql = "insert into runs values (?, ?, ?, ?, ?, ?)"
                self._db.execute(sql, 
                    [self.tag, self.inifile_name, 
                    self.sampler, date_string,
                    self.nchain, self.timestamp
                    ])

            #Create the table for the chain output itself
            types = {
                int: 'integer',
                float: 'double'
            }
            cols = ", ".join('"{1}" {0}'.format(types.get(c[1], "text"), c[0]) for c in self.columns)
            sql = "create table {0} ({1})".format(self._table_name, cols)
            self._db.execute(sql)


            #Create the metadata table
            sql = "create table {0} (key text, value text, comment text)".format(
                self._metadata_name)
            self._db.execute(sql)

    def _close(self):
        self._flush()
        self._db.close()

    def _flush_metadata(self):
        sql = "insert into {0} values (?, ?, ?)".format(self._metadata_name)
        with self._db:
            meta = [[k, v, c] for k,(v,c) in self._metadata.items()]
            self._db.executemany(sql, meta)
            self._metadata={}

        sql = "insert into {0} values (NULL, NULL, ?)".format(self._metadata_name)
        with self._db:
            self._db.executemany(sql, [[c] for c in self._comments])
        self._comments = []


    def _begun_sampling(self, params):
        #write the name line
        self.create_tables()
        self._flush_metadata()
        self._write_comment("STARTED_SAMPLING")

    def _write_metadata(self, key, value, comment=''):
        self._metadata[key]= (value, comment)

    def _write_comment(self, comment):
        self._comments.append(comment)

    def _write_parameters(self, params):
        self._params.append(params)

    def _write_final(self, key, value, comment=''):
        self._metadata[key]= (value, comment)

    def _flush(self):
        qs = "?"*len(self.columns)
        qs = ",".join(qs)
        sql = "insert into {0} values({1})".format(self._table_name, qs)
        with self._db:
            self._db.executemany(sql, self._params)
        self._params = []


    @classmethod
    def from_options(cls, options):
        #look something up required parameters in the ini file.
        #how this looks will depend on the ini 
        filename = options['filename']
        tag = options['tag']
        rank = options.get('rank', 0)
        nchain = options.get('parallel', 1)
        ini = options.get('inifile', '')
        sampler = options.get('sampler', 'unknown')

        return cls(filename, tag, sampler, ini, rank, nchain)

    @staticmethod
    def parse_time_stamp(table):
        end = -len("_chain")
        start = end - len(TIME_FORMAT_EXAMPLE)
        time_stamp_text = table[0][start:end]
        time_stamp = datetime.datetime.strptime(time_stamp_text,TIME_FORMAT)
        return time_stamp

    @classmethod
    def load_from_options(cls, options):
        filename = options['filename']
        tag = options['tag']
        conn = sqlite3.connect(filename)
        #we don't really need this except it is a conv
        with conn:
            sql = "select name from sqlite_master where name like '{}_%_chain'".format(tag)
            tables = conn.execute(sql).fetchall()
            tables = [(parse_time_stamp(table), table) for table in tables]
            #Find latest table
            tables.sort()

            if len(tables)==0:
                raise ValueError("Could not find data for a run with the tag you specified ({}) in the given file ({})".format(tag,filename))
            if len(tables)>1:
                print 
                print "Note: There are {} tables with the same tag in this file".format(len(tables))
                print "I am assuming you want the most recent one"
            
        #find

        ### more here
        return column_names, data, metadata, comments, final_metadata
