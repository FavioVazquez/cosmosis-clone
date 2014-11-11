from .output_base import OutputBase
from . import utils
import numpy as np
import os
from collections import OrderedDict
import sqlite3
import datetime




class SqliteOutput(OutputBase):
    FILE_EXTENSION = ".sq3"
    _aliases = ["sqlite", "sqlite3", "db"]

    def __init__(self, filename, tag, uuid, sampler, ini, rank=0, nchain=1):
        super(SqliteOutput, self).__init__()

        self._db = sqlite3.connect(filename)
        self.sampler = sampler
        self.nchain = nchain
        self.master = (rank==0)
        self.inifile_name = ini
        self.tag = tag
        self.uuid = uuid.hex
        self._name = "{0}_{1}_{2}_{3}".format(tag, rank+1, nchain, self.uuid)
        if self.master:
            self.setup_db_file()
        #also used to store comments:
        self._table_name = self._name+"_chain"
        self._metadata_name = self._name+"_meta"

        self._metadata = OrderedDict()
        self._comments = []
        self._params = []
        self._final_metadata = OrderedDict()

    def setup_db_file(self):
        sql = "create table if not exists runs \
        (tag text, ini text, sampler text, date text, nchain integer, uuid text)"
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
                    self.nchain, self.uuid
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
        rank = options.get('rank', 0)
        nchain = options.get('parallel', 1)
        tag = options.get('tag', 'cosmosis')
        ini = options.get('ini', '')
        uuid = options['uuid']
        sampler = options.get('sampler', 'unknown')

        return cls(filename, tag, uuid, sampler, ini, rank, nchain)

    @classmethod
    def load_from_options(cls, options):
        filename = options['filename']

        return column_names, data, metadata, comments, final_metadata
