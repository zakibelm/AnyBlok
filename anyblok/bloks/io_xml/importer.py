# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from lxml import etree


register = Declarations.register
IO = Declarations.Model.IO
ImporterException = Declarations.Exception.ImporterException


if_exist = 'update'
if_does_not_exist = 'create'
on_error = 'ignore'


@register(ImporterException)
class XMLImporterException(Exception):
    """ Simple exception for importer exception """


@register(IO)
class Importer:

    @classmethod
    def get_mode_choices(cls):
        res = super(Importer, cls).get_mode_choices()
        res.update({'Model.IO.Importer.XML': 'XML'})
        return res


@register(IO.Importer)
class XML:

    def __init__(self, importer):
        self.importer = importer
        self.error_found = []
        self.created_entries = []
        self.updated_entries = []
        self.params = {}
        self.two_way_external_id = {}

    def commit(self):
        if self.error_found:
            return False

        self.importer.commit()
        return True

    def _raise(self, msg, on_error=on_error, **kwargs):
        self.error_found.append(str(msg))
        if on_error == 'raise':
            raise ImporterException.XMLImporterException(msg)

    def find_entry(self, model=None, external_id=None, param=None, **kwargs):
        if (model, param) in self.params:
            return self.params[(model, param)]
        if model and external_id:
            if (model, external_id) in self.two_way_external_id:
                return self.two_way_external_id[(model, external_id)]

            entry = self.registry.IO.Mapping.get(model, external_id)
            if entry:
                return entry

        return None

    def check_entry_before_import(self, record, entry, if_exist=if_exist,
                                  if_does_not_exist=if_does_not_exist,
                                  **kwargs):
        if entry:
            if if_exist == 'pass':
                return True, entry
            elif if_exist == 'raise':
                self._raise("The tag %r (%r) already exist" % (
                    record.tag, record.attrib), **kwargs)
                # case of raise at the end, must not bloc import
                return True, None
        else:
            if if_does_not_exist == 'pass':
                return True, None
            elif if_does_not_exist == 'raise':
                self._raise("The tag %r (%r) does not exist" % (
                    record.tag, record.attrib), **kwargs)
                # case of raise at the end, must not bloc import
                return True, None

        return False, entry

    def import_entry(self, entry, values, model=None, external_id=None,
                     param=None, if_exist=if_exist,
                     if_does_not_exist=if_does_not_exist,
                     two_way=False, **kwargs):
        Model = self.registry.get(model)

        def update_x2M(entry, inValues, notInValues):
            for field in inValues.keys():
                if field in notInValues:
                    continue

                # temporaly deactivate auto flush to let time
                # orm to fill the remote column with foreign_key
                # which should be not null
                with self.registry.session.no_autoflush:
                    getattr(entry, field).extend(inValues[field])

        def create_entry():
            try:
                insert_values = {x: y for x, y in values.items()
                                 if not isinstance(y, list)}
                if two_way:
                    return_entry = Model(**insert_values)
                else:
                    return_entry = Model.insert(**insert_values)

                update_x2M(return_entry, values, insert_values)
                self.created_entries.append(return_entry)
                return return_entry
            except Exception as e:
                self._raise(e, **kwargs)

        return_entry = entry
        if entry:
            if if_exist == 'continue':
                return_entry = entry
            elif if_exist == 'create':
                return_entry = create_entry()
            elif if_exist == 'update':
                try:
                    insert_values = {x: y for x, y in values.items()
                                     if not isinstance(y, list)}
                    if insert_values:
                        entry.update(values)

                    update_x2M(entry, values, insert_values)
                    self.updated_entries.append(entry)
                except Exception as e:
                    self._raise(e, **kwargs)
        else:
            if if_does_not_exist == 'create':
                return_entry = create_entry()

        if return_entry:
            if model and param:
                if (model, param) not in self.params:
                    self.params[(model, param)] = return_entry
                else:
                    if self.params[(model, param)] != return_entry:
                        self._raise("Overwrite the params (%r, %r)" % (
                            model, param), **kwargs)

            if external_id:
                if two_way:
                    self.two_way_external_id[(
                        model, external_id)] = return_entry
                else:
                    self.registry.IO.Mapping.set(external_id, return_entry)

        return return_entry

    def import_multi_values(self, records, model):
        vals = []
        for record in records:
            val = self.import_record(record, model=model, two_way=True)
            if not val:
                continue

            vals.append(val)

        return vals

    def import_value(self, record, ctype, model, on_error=on_error):
        val = self.import_record(record, model=model)
        if ctype in ('One2One', 'Many2One'):
            return val
        else:
            if not val:
                return None

            pks = val.to_primary_keys()
            vals = [x for x in pks.values()]
            if len(vals) > 1:
                self._raise(
                    "Multi foreign key for %r (%r) are not "
                    "implemented" % (record.tag, record.attrib),
                    on_error=on_error)

            return vals[0]

    def import_field(self, field, ctype, model=None, on_error=on_error):
        if 'model' in field.attrib:
            model = field.attrib['model']

        param = field.attrib.get('param')

        if param:
            if model:
                if (model, param) in self.params:
                    return self.params[(model, param)]

            else:
                self._raise('Param %r waiting for None model ' % param,
                            on_error=on_error)

        val = None
        external_id = False
        if 'external_id' in field.attrib:
            external_id = True
            val = field.attrib['external_id']
        else:
            val = field.text

        try:
            res = None
            if ctype in ('Many2One', 'One2One') and external_id:
                if model and (model, val) in self.two_way_external_id:
                    res = self.two_way_external_id[(model, val)]

            if not res:
                res = self.importer.str2value(val, ctype,
                                              external_id=external_id,
                                              model=model)
            if param:
                self.params[(model, param)] = res

            return res
        except Exception as e:
            self._raise(e, on_error=on_error)
            return None

    def import_record(self, record, two_way=False, **kwargs):
        kwargs.update(record.attrib)
        _kw = {}
        if 'on_error' in kwargs:
            _kw['on_error'] = kwargs['on_error']

        entry = self.find_entry(**kwargs)
        mustbereturned, entry = self.check_entry_before_import(
            record, entry, **kwargs)

        if mustbereturned:
            return entry

        if 'model' not in kwargs:
            self._raise("No model found for record %r (%r)" % (
                record.tag, kwargs), **_kw)
            return None

        Model = self.registry.get(kwargs['model'])
        fields_description = Model.fields_description()
        values = {}
        for field in record.getchildren():
            if 'on_error' in field.attrib:
                _kw['on_error'] = field.attrib['on_error']

            if field.tag is etree.Comment:
                continue

            if field.tag.lower() != 'field':
                self._raise("Waitting 'field' node, not %r" % field.tag, **_kw)
                continue

            if 'name' not in field.attrib:
                self._raise("field %r (%r) have not attribute name" % (
                    field.tag, field.attrib), **_kw)
                continue

            field_name = field.attrib['name']
            if field_name not in fields_description:
                self._raise('Model %r have not field %r' % (
                    Model.__registry_name__, field_name))
                continue

            field_model = fields_description[field_name]['model']
            field_type = fields_description[field_name]['type']
            children = field.getchildren()

            if children:
                if field_type in ('One2Many', 'Many2Many'):
                    vals = self.import_multi_values(children, field_model)
                    if vals:
                        values[field_name] = vals

                else:
                    values[field_name] = self.import_value(
                        field, field_type, field_model, **_kw)

            else:
                values[field_name] = self.import_field(
                    field, field_type, model=field_model, **_kw)

        return self.import_entry(entry, values, two_way=two_way, **kwargs)

    def import_records(self, records):
        for record in records.getchildren():
            if record.tag is etree.Comment:
                continue
            elif record.tag.lower() == 'record':
                self.import_record(record, model=self.importer.model)
            elif record.tag.lower() == 'commit':
                self.commit()
            else:
                self._raise('%r is not known' % record.tag, **records.attrib)

    def run(self):
        records = etree.fromstring(self.importer.file_to_import)
        if records.tag.lower() == 'records':
            self.import_records(records)
        else:
            self._raise('%r is not known' % records.tag)

        if self.error_found:
            if records.attrib.get('on_error', 'raise') == 'raise':
                msg = "Exception found : \n %s" % '\n'.join(self.error_found)
                raise ImporterException.XMLImporterException(msg)

        return {
            'error_found': self.error_found,
            'created_entries': self.created_entries,
            'updated_entries': self.updated_entries,
        }

    @classmethod
    def insert(cls, delimiter=None, quotechar=None, **kwargs):
        kwargs['mode'] = cls.__registry_name__
        if 'model' not in kwargs:
            raise ImporterException.CSVImporterException(
                "The column 'model' is required")

        if not isinstance(kwargs['model'], str):
            kwargs['model'] = kwargs['model'].__registry_name__

        return cls.registry.IO.Importer.insert(**kwargs)