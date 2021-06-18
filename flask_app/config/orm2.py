from flask import flash
from flask_app import DB
import math,pymysql.cursors

class QuerySet:
    def __init__(self,model,query,data=None):
        self._model = model
        self._query = query
        self._data = data
        self._collection = None
        self._config = {}

    def order_by(self,**config):
        self._config['rand'] = config.get('rand')
        self._config['column'] = config.get('column','id')
        self._config['desc'] = config.get('desc')
        self._config['count'] = config.get('count')
        return self

    def exclude(self,*args):
        total = args[0]
        for arg in args:
            total += arg
        self._config['exclude'] = total._query
        return self

    def intersect(self,other):
        self._config['intersect'] = other
        return self

    def first(self):
        self._config['limit'] = 1
        return self[0]
    
    def last(self):
        self._config['limit'] = 1
        self._config['desc'] = True
        return self[-1]

    def get(self,**data):
        for item in self:
            for k,v in data.items():
                if getattr(item,k,None) != v:
                    break
            else:
                return item

    def __len__(self):
        if not isinstance(self._collection,list):
            self._collection = self.__retrieve__();
        return len(self._collection)

    def _count(self,attr):
        col = getattr(self._model(),attr)
        if isinstance(col,MtM):
            return f"LEFT JOIN `{col.middle}` ON `{col.right_name}_id`=`{col.right.table}`.id GROUP BY `{col.right.table}`.id ORDER BY COUNT(`{col.right.table}`.id) "
        elif isinstance(col,QuerySet):
            col_name = None
            for k in col._data:
                if 'id' in k:
                    col_name = k
                    break
            return f"LEFT JOIN `{col._model().table}` AS `table2` ON `{col_name}`=`table2`.id GROUP BY `table2`.id ORDER BY COUNT(`{col_name}`) "
        return f"ORDER BY COUNT({attr}) "

    def __retrieve__(self):
        config = ""
        if self._config:
            #COUNT
            if count := self._config.get('count'):
                config += self._count(count)
            else:
                #EXCLUDE
                if exclude := self._config.get('exclude'):
                    q_split = exclude.split('.*')
                    formatted = " `id`".join([s.rsplit(' ',1)[:-1][0] for s in q_split[:-1]]+[q_split[-1]])
                    config += f"{'WHERE ' if 'WHERE' not in self._query else 'AND '}`id` NOT IN ({formatted}) "
                #INTERSECT
                elif intersect := self._config.get('intersect'):
                    q_split = intersect.split('.*')
                    formatted = " `id`".join([s.rsplit(' ',1)[:-1][0] for s in q_split[:-1]]+[q_split[-1]])
                    config += f"{'WHERE ' if 'WHERE' not in self._query else 'AND '}`id` IN ({formatted}) "
                #ORDER BY
                config += "ORDER BY "
                if self._config.get('rand'):
                    config += "RAND() "
                elif column := self._config.get('column','id'):
                    config += f"`{column}` "
            #DESC
            if self._config.get('desc'):
                config += "DESC "
            #LIMIT
            if limit := self._config.get('limit'):
                config += f"LIMIT {limit}"
        query = f"{self._query} {config}"
        results = [self._model(**item) for item in connectToMySQL(DB).query_db(query)]
        self._config = {}
        return results

    def __iter__(self):
        self.n = 0
        self.max = len(self)
        return self

    def __next__(self):
        if self.n < self.max:
            result = self._collection[self.n]
            self.n += 1
            return result
        else:
            raise StopIteration

    def __add__(self,other):#allows for addition operator to do concatenation
        if not isinstance(other,self.__class__):
            raise TypeError(f"Both collections must be {self.__class__.__name__} instances to concatenate!")
        if not self._model == other._model:
            raise TypeError(f"Both {self.__class__.__name__}s should contain instances of type {self._model.__name__}!")
        query = f"{self._query} UNION DISTINCT {other._query}"
        return QuerySet(self._model,query)

    def __sub__(self,other):#allows for subtraction operator to get difference
        if not isinstance(other,self.__class__):
            raise TypeError(f"Both items must be {self.__class__.__name__} instances to get the difference!")
        if not self._model == other._model:
            raise TypeError(f"Both {self.__class__.__name__}s should contain instances of type {self._model.__name__}!")
        query = f"{self._query} EXCEPT {other._query}"
        return QuerySet(self._model,query)

    def __repr__(self):#more readable representation
        return f"<{self.__class__.__name__}: collection=({', '.join(str(item) for item in self)})>"

    def __getitem__(self,key):
        if type(key) is not int:
            raise TypeError("index must be of type int!")
        if type(key) is int and (key < 0 and math.abs(key)-1 < len(self)) or key < len(self):
            return self._collection[key]

    def __setitem__(self,*args):
        raise AttributeError(f"{self.__class__.__name__} cannot be modified directly!")

class MtM(QuerySet):
    def __init__(self,middle=None,**kwargs):
        self._collection = None
        self._config = {}
        if not isinstance(middle,str):
            raise TypeError("Middle table name should be a string!")
        self.middle = middle
        items = list(kwargs.items())
        if len(items) == 2:
            (self.left_name,self.left),(self.right_name,self.right) = items
            if not isinstance(self.left,Model):
                raise TypeError("Left table should be an instance of a class inheriting from Model!")
            if not issubclass(self.right,Model):
                raise TypeError("Right table should be a class inheriting from Model!")
            self._query = f"SELECT `{self.right_name}`.* FROM `{self.right.table}` AS `{self.right_name}` JOIN `{self.middle}` ON `{self.right_name}_id` = `{self.right_name}`.id WHERE `{self.left_name}_id`={self.left.id}"
            self._model = self.right
        else:
            raise AttributeError("MtM takes 1 argument (middle_table:str) and 2 key-word arguments (left_table:instance, right_table:Class)!")

    def add(self, *items):
        for item in items:
            if not isinstance(item,self.right):
                raise TypeError(f"Item to add must be of type {self.right.__name__}!")
        query = f"INSERT INTO `{self.middle}` (`{self.left_name}_id`,`{self.right_name}_id`) VALUES {', '.join(f'({self.left.id},{item.id})' for item in items)}"
        return connectToMySQL(DB).query_db(query)

    def remove(self,*items):
        for item in items:
            if not isinstance(item,self.right):
                raise TypeError(f"Item to remove must be of type {self.right.__name__}!")
        query = f"DELETE FROM `{self.middle}` WHERE `{self.left_name}_id`={self.left.id} AND `{self.right_name}_id` IN ({', '.join(str(item.id) for item in items)})"
        return connectToMySQL(DB).query_db(query)

    def __repr__(self):#more readable representation
        return f"<{self.__class__.__name__}: table={self.middle}, collection=({', '.join(str(item) for item in self)})>"

class MySQLConnection:
    def __init__(self, db=DB):
        self.connection = pymysql.connect(
            host = 'localhost',
            user = 'root',
            password = 'root', 
            db = db,
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor,
            autocommit = True
        )

    def sanitize_data(self,query,data):
        with self.connection.cursor() as cursor:
            try:
                query = cursor.mogrify(query, data)
                return query
            except Exception as e:
                print("Something went wrong", e)
                return False

    def query_db(self, query):
        with self.connection.cursor() as cursor:
            try:
                print("Running Query:", query)
                cursor.execute(query)
                if query.lower().startswith("select"):
                    return cursor.fetchall()
                self.connection.commit()
                if query.lower().startswith("insert"):
                    return cursor.lastrowid
            except Exception as e:
                print("Something went wrong", e)
                return False
            finally:
                self.connection.close()

def connectToMySQL(db):
    return MySQLConnection(db)

class Model:
#-------------------Create---------------------#
    @classmethod
    def create(cls, **data):
        query = f"INSERT INTO `{cls.table}` ({', '.join(f'`{col}`' for col in data.keys())}) VALUES ({', '.join(f'%({col})s' for col in data.keys())})"
        connection = connectToMySQL(DB)
        query = connection.sanitize_data(query,data)
        return connection.query_db(query)
#-------------------Retrieve-------------------#
    @classmethod
    def retrieve(cls,**data):
        query = f"SELECT `{cls.table}`.* FROM `{cls.table}` {'WHERE'+' AND'.join(f' `{col}`=%({col})s' for col in data.keys()) if data else ''}"
        connection = connectToMySQL(DB)
        query = connection.sanitize_data(query,data)
        connection.connection.close()
        return QuerySet(cls,query,data)
#-------------------Update---------------------#
    @classmethod
    def update(cls,id=None,**data):
        query = f"UPDATE `{cls.table}` SET {', '.join(f'`{col}`=%({col})s' for col in data.keys())} {f'WHERE `id`={id}' if id else ''}"
        connection = connectToMySQL(DB)
        query = connection.sanitize_data(query,data)
        return connection.query_db(query)
#-------------------Delete---------------------#
    @classmethod
    def delete(cls, **data):
        query = f"DELETE FROM `{cls.table}` WHERE {' AND '.join(f'`{col}`=%({col})s' for col in data.keys())}"
        connection = connectToMySQL(DB)
        query = connection.sanitize_data(query,data)
        return connection.query_db(query)
#------------------Validate--------------------#
    @classmethod
    def validate(cls, **data):
        is_valid = True
        for field,val in data.items():
            for valid,msg,kwargs in cls.validators.get(field,[]):
                kwargs = {k:data.get(v) for k,v in kwargs.items()}
                if not valid(val,**kwargs):
                    flash(msg,f"{cls.__name__}.{field}")
                    is_valid = False
                    # break#limits to one validation per field at a time
        return is_valid

    @classmethod
    def validator(cls,msg,**kwargs):
        def register(func):
            cls.validators = getattr(cls,"validators",{})
            cls.validators[func.__name__] = cls.validators.get(func.__name__,[])
            cls.validators[func.__name__].append((func,msg,kwargs))
        return register
#----------------------------------------------#
    def __new__(cls,*args,**kwargs):#delete and update implictly pass id when called from instance
        inst = super().__new__(cls)
        inst.delete = lambda : cls.delete(id=inst.id)
        inst.update = lambda **data : cls.update(id=inst.id,**data)
        return inst

    def __repr__(self):#more readable representation
        return f"<{self.__class__.__name__}: id={self.id}>"

    def __lt__(self,other):#allows sorting by id
        return self.id < other.id

    def __eq__(self,other):#allows checking equality
        return self.id == other.id

def table(table):
    if type(table) is str:
        def inner(cls):
            setattr(cls,"table",table)
            return cls
        return inner
    setattr(table,"table",table.__name__.lower()+"s")
    return table