# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
register = Declarations.register
System = Declarations.Model.System
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean


@register(System)
class RelationShip(Mixin.Field):

    rtype = String(label="Type", nullable=False)
    local_column = String()
    remote_column = String()
    remote_name = String()
    remote_model = String(nullable=False)
    remote = Boolean(default=False)
    nullable = Boolean()

    @classmethod
    def add_field(cls, rname, relation, model, table):
        """ Insert a relationship definition

        :param rname: name of the relationship
        :param relation: instance of the relationship
        :param model: namespace of the model
        :param table: name of the table of the model
        """
        local_column = relation.info.get('local_column')
        remote_column = relation.info.get('remote_column')
        remote_model = relation.info.get('remote_model')
        remote_name = relation.info.get('remote_name')
        label = relation.info.get('label')
        nullable = relation.info.get('nullable', True)
        rtype = relation.info.get('rtype')
        if rtype is None:
            return

        vals = dict(code=table + '.' + rname,
                    model=model, name=rname, local_column=local_column,
                    remote_model=remote_model, remote_name=remote_name,
                    remote_column=remote_column, label=label,
                    nullable=nullable, rtype=rtype)
        cls.insert(**vals)

        if remote_name:
            remote_type = "Many2One"
            if rtype == "Many2One":
                remote_type = "One2Many"
            elif rtype == 'Many2Many':
                remote_type = "Many2Many"
            elif rtype == "One2One":
                remote_type = "One2One"

            m = cls.registry.get(remote_model)
            vals = dict(code=m.__tablename__ + '.' + remote_name,
                        model=remote_model, name=remote_name,
                        local_column=remote_column, remote_model=model,
                        remote_name=rname,
                        remote_column=local_column, label=label,
                        nullable=True, rtype=remote_type, remote=True)
            cls.insert(**vals)
