from flask import flash
from flask_app.config.mysqlconnection import connectToMySQL
from flask_app import DB

class Schema:
    '''
    A class to that holds methods for basic sql queries.

    Classes that represent tables in your database should
    extend this class.

    Should only ever be extended and not instantiated on its own.
    '''
    @classmethod
    def order_by(cls,col="id",desc=False,rand=False):
        config = {
            "order_by" : col,
            "desc" : desc,
            "rand" : rand
        }
        setattr(cls,"config",config)
        return cls

#-------------------Create---------------------#
    @classmethod
    def create(cls, **data):
        '''
        Creates a new row in the database built from the given data.

        Example usages:
        --------------
            ``User.create(name="John",age=35) -> creates a new user with name "John" and age of 35``

            ``User.create(**request.form) -> creates a new user based on the data recieved from the form``

        Parameters
        ----------
            data (str): Key word arguments for each of the columns and the values to create.

        Returns
        -------
            Id of the newly created row or False if query failed.
        '''
        query = f"INSERT INTO `{cls.table}` ({', '.join(f'`{col}`' for col in data.keys())}) VALUES ({', '.join(f'%({col})s' for col in data.keys())})"
        return connectToMySQL(DB).query_db(query,data)
#-------------------Retrieve-------------------#
    @classmethod
    def retrieve_all(cls, **data):
        '''
        Retrieves everything from the database that matches the given data in the form of a list.

        If no parameters are given, everything from that table will be returned.

        Example usages:
        --------------
            ``User.retrieve() -> returns a list of all users``

            ``User.retrieve(id=1) -> returns a single user matching the id``

            ``User.retrieve(name="John") -> returns a list of all users with the name "John"``

        Parameters
        ----------
            data (**str) : Key word arguments for each of the column names and the values to try and match.

        Returns
        -------
            List of class instances created from the matching rows in the database.
        '''
        config = getattr(cls,'config',None)
        if config:
            config = f"ORDER BY {'RAND()' if config['rand'] else config['col']} {'DESC' if config['desc'] else 'ASC'}"
            delattr(cls,"config")
        query = f"SELECT * FROM `{cls.table}` {'WHERE'+' AND'.join(f' `{col}`=%({col})s' for col in data.keys()) if data else ''} {config if config else ''}"
        return [cls(**item) for item in  connectToMySQL(DB).query_db(query,data)]

    @classmethod
    def retrieve_one(cls, **data):
        '''
        Retrieves everything from the database that matches the given data in the form of a list.

        If no parameters are given, everything from that table will be returned.

        Example usages:
        --------------
            ``User.retrieve() -> returns a list of all users``

            ``User.retrieve(id=1) -> returns a single user matching the id``

            ``User.retrieve(name="John") -> returns a list of all users with the name "John"``

        Parameters
        ----------
            data (**str) : Key word arguments for each of the column names and the values to try and match.

        Returns
        -------
            List of class instances created from the matching rows in the database or False if query failed.
        '''
        config = getattr(cls,'config',None)
        if config:
            config = f"ORDER BY {config['rand'] if config['rand'] else config['col']} {'DESC' if config['desc'] else 'ASC'}"
            delattr(cls,"config")
        query = f"SELECT * FROM `{cls.table}` {'WHERE'+' AND'.join(f' `{col}`=%({col})s' for col in data.keys()) if data else ''} {config if config else ''} LIMIT 1"
        result = connectToMySQL(DB).query_db(query,data)
        if result:
            result = cls(**result[0])
        return result
#-------------------Update---------------------#
    @classmethod
    def update(cls,id=None,**data):#TODO allow for filter dict paramater instead of id
        '''
        Updates the target instance in the database with the given data.

        Example usages:
        --------------
            ``User.update(1,name="Joe",age=24) -> updates user with id of 1 to have name of "Joe" and age of "24"

            ``User.update(name="John") -> updates ALL users to have the name "John"

            ``my_user.update(name="Joe",age=24) -> updates my_user to now have the name of "Joe" and age of 24``

            ``my_user.update(**request.form) -> updates my_user based on the data recieved from the form``

        Parameters
        ----------
            id (str) : Id of instance to update (implicit if called on instance)

            data (**str) : Key word arguments for each of the column names and the new values to update with.

        Returns
        -------
            None if successful or False if query failed.
        '''
        query = f"UPDATE `{cls.table}` SET {', '.join(f'`{col}`=%({col})s' for col in data.keys())} {f'WHERE `id`={id}' if id else ''}"
        return connectToMySQL(DB).query_db(query,data)
#-------------------Delete---------------------#
    @classmethod
    def delete(cls, **data):
        '''
        Deletes all rows from the database that match the given data.

        Example usages:
        --------------
            ``User.delete(id=1) -> deletes user with the id of 1``

            ``User.delete(name="John") -> deletes all users with the name "John"``

            ``my_user.delete() -> deletes user based on instance``

        Parameters
        ----------
            data (**str) : Key word arguments for each of the column names and the values to try and match.

        Returns
        -------
            None if successful or False if query failed.
        '''
        query = f"DELETE FROM `{cls.table}` WHERE {' AND '.join(f'`{col}`=%({col})s' for col in data.keys())}"
        return connectToMySQL(DB).query_db(query,data)
#------------------Validate--------------------#
    @classmethod
    def validate(cls, **data):
        '''
        Validates the given data by applying any validators registered to the class via the validator decorator.

        If no validators are registered, then the data will always be considered valid.

        Example usages:
        --------------
            ``User.validate(**request.form) -> validates data from form``

            ``User.validate(name="abc",age="24") -> validates the given attributes``

        Parameters
        ----------
            data (**str) : Key word arguments for each of the field names and the values to be validated.

        Returns
        -------
            Boolean determining whether all of the data is valid or not
        '''
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
        '''
        Decorator used to register validators to a given class.

        The method below the decorator should be named the exact same
        as the field you are trying to validate and should return a boolean
        which will be used to determine if the field is valid or not. Flashed
        message categories will be accessed as "Class.field" format.

        Parameters
        ----------
            msg (str): Error message for the specific validation

            kwargs (**str): Key word arguments for any extra fields that should be passed into the validation function
        '''
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
        return f"<{self.table} obj: id={self.id}>"

    def __eq__(self,other):#allows for checking equality
        return self.id == other.id
    
    def __lt__(self,other):#allows for checking lessthan (used for sorting)
        return self.id < other.id

    def __hash__(self):#allows or hashing and using in a set
        return hash(self.id)

class MtM:#TODO maybe implement a seperate collection class that both MtM and schema use for returning query data so that way they can work together
    def __init__(self,middle=None,**kwargs):
        '''
        Create an instance of the MtM class. Foreign key names should be
        the table name lowercase and pluralized to work correctly (currently)

        Example usages:
        --------
            ``self.likes = Mtm("likes",liker=self,liked=User) -> creates a many-to-many relationship with User called likes ('_id' will be appended to the column name automatically when querying)``

        Attributes:
        ----------
            middle (str): Table name of the middle table in the relationship.

            left_table (Schema): Instance of class representing a given row in a table. Can give an optional key-name if column name is not the default in your table.

            right_table (Class): Class associated with the table to create the relationship with. Can give an optional key-name if column name is not the default in your table.
        '''
        if not isinstance(middle,str):
            raise TypeError("Middle table name should be a string!")
        self._collection = None
        self.middle = middle
        items = list(kwargs.items())
        if len(items) == 2:
            (self.left_name,self.left),(self.right_name,self.right) = items
            if not isinstance(self.left,Schema):
                raise TypeError("Left table should be an instance of a class inheriting from Schema!")
            if not issubclass(self.right,Schema):
                raise TypeError("Right table should be a class inheriting from Schema!")
        else:
            raise AttributeError("MtM takes 1 argument (middle_table:str) and 2 key-word arguments (left_table:instance, right_table:Class)!")

    def add(self, *items):
        """
        Creates a new relationship between the given instance and any instances passed in as arguments.

        Example usages:
        -------------
            ``my_user.favorites.add(my_book) -> adds relationship to given book``

            ``my_user.favorites.add(*Book.retrieve_all()) -> adds relationship to all existing books``

        Parameters
        ----------
            items (Schema): Item(s) passed as arguments to have a relationship with the given instance.

        Returns
        -------
            Id of the new relationship created in the database if successful or False if query failed.
        """
        for item in items:
            if not isinstance(item,self.right):
                raise TypeError(f"Item to add must be of type {self.right.__name__}!")
        query = f"INSERT INTO `{self.middle}` (`{self.left_name}_id`,`{self.right_name}_id`) VALUES {', '.join(f'({self.left.id},{item.id})' for item in items)}"
        return connectToMySQL(DB).query_db(query)

    def remove(self,*items):
        """
        Removes relationship from given instance and any instances passed in as arguments.

        Example usages:
        -------------
            ``my_user.favorites.remove(my_book) -> removes relationship to given book``

            ``my_user.favorites.remove(*Book.retrieve_all()) -> removes relationship from all existing books``

        Parameters
        ----------
        items (Schema): Item(s) to have relationship with the given instance removed.

        Returns
        -------
            None if successful or False if query failed
        """
        for item in items:
            if not isinstance(item,self.right):
                raise TypeError(f"Item to remove must be of type {self.right.__name__}!")
        query = f"DELETE FROM `{self.middle}` WHERE `{self.left_name}_id`={self.left.id} AND `{self.right_name}_id` IN ({', '.join(str(item.id) for item in items)})"
        return connectToMySQL(DB).query_db(query)

    def intersect(self,other):#returns the intersection (shared items) of two MtM instances
        if not isinstance(other,MtM):
            raise TypeError("Can only intersect MtM instances!")
        if not isinstance(self._collection,list):
            self._collection = self.__retrieve__()
        if not isinstance(other._collection,list):
            other._collection = other.__retrieve__()
        return [item for item in self._collection if item in other._collection]

    def __retrieve__(self):#custom dunder method, not actually overriding anything here, but still should only ever be called internally
        config = getattr(self.left,'config',None)
        if config:
            config = f"ORDER BY {config['rand'] if config['rand'] else config['col']} {'DESC' if config['desc'] else 'ASC'}"
            delattr(self.left,"config")
        query = f"SELECT `{self.right_name}`.* FROM `{self.right.table}` AS {self.right_name} JOIN `{self.middle}` ON `{self.right_name}_id` = `{self.right_name}`.id WHERE `{self.left_name}_id`={self.left.id} {config if config else ''}"
        return [self.right(**item) for item in connectToMySQL(DB).query_db(query)]

    def __repr__(self):#more readable representation
        return f"<MtM obj: table={self.middle}, collection=({', '.join(str(item) for item in self)})>"

    def __iter__(self):#allows for iteration
        if not isinstance(self._collection,list):#lazy loading, only retrieve the data if it hasn't already been cached
            self._collection = self.__retrieve__()
        self.n = 0
        self.max = len(self)
        return self

    def __next__(self):#allows for iteration
        if self.n < self.max:
            result = self._collection[self.n]
            self.n += 1
            return result
        else:
            raise StopIteration

    def __len__(self):#allows for checking length
        if not isinstance(self._collection,list):#lazy loading, only retrieve the data if it hasn't already been cached
            self._collection = self.__retrieve__()
        return len(self._collection)

    def __add__(self,other):#allows for addition operator to do concatenation
        if not isinstance(other,MtM):
            raise TypeError("Both items must be MtM instances to concatenate!")
        if not isinstance(self._collection,list):
            self._collection = self.__retrieve__()
        if not isinstance(other._collection,list):
            other._collection = other.__retrieve__()
        return self._collection + other._collection

    def __sub__(self,other):#allows for subtraction operator to get difference
        if not isinstance(other,MtM):
            raise TypeError("Both items must be MtM instances to get the difference!")
        if not isinstance(self._collection,list):
            self._collection = self.__retrieve__()
        if not isinstance(other._collection,list):
            other._collection = other.__retrieve__()
        return [item for item in other._collection if item not in self._collection]