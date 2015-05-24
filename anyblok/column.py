# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey, Sequence


@Declarations.add_declaration_type()
class Column(Declarations.Field):
    """ Column class

    This class can't be instanciated
    """

    foreign_key = None
    sqlalchemy_type = None

    def __init__(self, *args, **kwargs):
        """ Initialize the column

        :param label: label of this field
        :type label: str
        """
        self.forbid_instance(Column)
        assert self.sqlalchemy_type
        self.sequence = None

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            self.foreign_key = kwargs.pop('foreign_key')

        if 'sequence' in kwargs:
            self.sequence = Sequence(kwargs.pop('sequence'))

        self.db_column_name = None
        if 'db_column_name' in kwargs:
            self.db_column_name = kwargs.pop('db_column_name')

        super(Column, self).__init__(*args, **kwargs)

    def native_type(cls):
        """ Return the native SqlAlchemy type """
        return cls.sqlalchemy_type

    def get_tablename(self, registry, model):
        """ Return the table name of the remote model

        :rtype: str of the table name
        """
        if isinstance(model, str):
            model = registry.loaded_namespaces_first_step[model]
            return model['__tablename__']
        else:
            return model.__tablename__

    def get_registry_name(self, model):
        """ Return the registry name of the remote model

        :rtype: str of the registry name
        """
        if isinstance(model, str):
            return model
        else:
            return model.__registry_name__

    def format_foreign_key(self, registry, args, kwargs):
        if self.foreign_key:
            model, col = self.foreign_key
            tablename = self.get_tablename(registry, model)
            foreign_key = tablename + '.' + col
            args = args + (ForeignKey(foreign_key),)
            kwargs['info']['foreign_key'] = foreign_key
            kwargs['info']['remote_model'] = self.get_registry_name(model)

        return args

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: known properties of the model
        :rtype: sqlalchemy column instance
        """
        self.format_label(fieldname)
        args = self.args
        kwargs = self.kwargs.copy()
        if 'info' not in kwargs:
            kwargs['info'] = {}
        args = self.format_foreign_key(registry, args, kwargs)
        kwargs['info']['label'] = self.label
        if self.sequence:
            args = (self.sequence,) + args

        if self.db_column_name:
            db_column_name = self.db_column_name
            kwargs['info']['use_db_column_name'] = db_column_name
        else:
            db_column_name = fieldname

        return SA_Column(db_column_name, self.sqlalchemy_type, *args, **kwargs)

    def must_be_declared_as_attr(self):
        """ Return True if the column have a foreign key to a remote column """
        if self.foreign_key is not None:
            return True

        return False
