# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from random import random
from anyblok.tests.testcase import DBTestCase
from anyblok.declarations import Declarations, cache, classmethod_cache
from anyblok.bloks.anyblok_core.exceptions import CacheException
register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


def wrap_cache(condition):

    def wrapper(function):
        return function

    if condition:
        return cache()

    return wrapper


def wrap_cls_cache(condition):
    if condition:
        return classmethod_cache()

    return classmethod


class TestCache(DBTestCase):

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def test_cache_invalidation(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        Cache = self.registry.System.Cache
        nb_invalidation = Cache.query().count()
        Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Cache.query().count(), nb_invalidation + 1)

    def test_invalid_cache_invalidation(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        Cache = self.registry.System.Cache
        with self.assertRaises(CacheException):
            Cache.invalidate('Model.Test2', 'method_cached')

    def test_detect_cache_invalidation(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        Cache = self.registry.System.Cache
        self.assertEqual(Cache.detect_invalidation(), False)
        Cache.insert(registry_name="Model.Test", method="method_cached")
        self.assertEqual(Cache.detect_invalidation(), True)

    def test_get_invalidation(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        Cache = self.registry.System.Cache
        Cache.insert(registry_name="Model.Test", method="method_cached")
        caches = Cache.get_invalidation()
        self.assertEqual(len(caches), 1)
        cache = caches[0]
        self.assertEqual(cache.indentify, ('Model.Test', 'method_cached'))


class TestSimpleCache(DBTestCase):

    def check_method_cached(self, Model, registry_name, value=1):
        m = Model()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertEqual(m.method_cached(), 2 * value)

    def check_method_cached_invalidate_all(self, Model, value=1):
        m = Model()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate_all()
        self.assertEqual(m.method_cached(), 2 * value)

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_by_mixin_chain(self):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)
        class MTest2(Mixin.MTest):
            pass

        @register(Model)
        class Test(Mixin.MTest2):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            @wrap_cache(withcore)
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)
        class MTest:

            y = 0

            @wrap_cache(withmixin)
            def method_cached(self):
                self.y += 2
                return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            @wrap_cache(withmodel)
            def method_cached(self):
                self.z += 3
                return self.z + super(Test, self).method_cached()

    def test_model(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_model2(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_core(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_core2(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_mixin2(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_mixin_chain(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin_chain)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_mixin_chain2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin_chain)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = self.registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = self.registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = self.registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = self.registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = self.registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_invalidate_all_check_model(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        self.check_method_cached_invalidate_all(self.registry.Test)

    def test_invalidate_all_check_core(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        self.check_method_cached_invalidate_all(self.registry.Test)

    def test_invalidate_all_check_mixin(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        self.check_method_cached_invalidate_all(self.registry.Test)


class TestClassMethodCache(DBTestCase):

    def check_method_cached(self, Model, registry_name):
        m = Model
        value = m.method_cached()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertNotEqual(m.method_cached(), value)

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_by_mixin_chain(self):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)
        class MTest2(Mixin.MTest):
            pass

        @register(Model)
        class Test(Mixin.MTest2):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            @wrap_cls_cache(withcore)
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)
        class MTest:

            y = 0

            @wrap_cls_cache(withmixin)
            def method_cached(cls):
                cls.y += 2
                return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            @wrap_cls_cache(withmodel)
            def method_cached(cls):
                cls.z += 3
                return cls.z + super(Test, cls).method_cached()

    def test_model(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_model2(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_core(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_core2(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_mixin2(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_mixin_chain(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin_chain)
        self.check_method_cached(self.registry.Test, 'Model.Test')

    def test_mixin_chain2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin_chain)
        from anyblok import Declarations
        self.check_method_cached(self.registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = self.registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = self.registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = self.registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = self.registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = self.registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        self.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)


class TestInheritedCache(DBTestCase):

    def check_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 6)

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        self.check_method_cached(self.registry.Test)

    def test_model2(self):
        self.reload_registry_with(self.add_model_with_method_cached,
                                  inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)

    def test_core(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        self.check_method_cached(self.registry.Test)

    def test_core2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)

    def test_mixin(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(self.registry.Test)

    def test_mixin2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)


class TestInheritedClassMethodCache(DBTestCase):

    def check_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 6)

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        self.reload_registry_with(self.add_model_with_method_cached)
        self.check_method_cached(self.registry.Test)

    def test_model2(self):
        self.reload_registry_with(self.add_model_with_method_cached,
                                  inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)

    def test_core(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_core)
        self.check_method_cached(self.registry.Test)

    def test_core2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)

    def test_mixin(self):
        self.reload_registry_with(self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(self.registry.Test)

    def test_mixin2(self):
        self.reload_registry_with(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(self.registry.Test)


class TestComparatorInterModel(DBTestCase):

    def check_comparator(self):
        Test = self.registry.Test
        Test2 = self.registry.Test2
        self.assertEqual(Test.method_cached(), Test.method_cached())
        self.assertEqual(Test2.method_cached(), Test2.method_cached())
        self.assertNotEqual(Test.method_cached(), Test2.method_cached())

    def test_model(self):

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test2:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

        self.reload_registry_with(add_in_registry)
        self.check_comparator()

    def test_mixin(self):

        def add_in_registry():

            @register(Mixin)
            class MTest:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test(Mixin.MTest):
                pass

            @register(Model)
            class Test2(Mixin.MTest):

                pass

        self.reload_registry_with(add_in_registry)
        self.check_comparator()

    def test_core(self):

        def add_in_registry():

            @register(Core)
            class Base:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test:
                pass

            @register(Model)
            class Test2:

                pass

        self.reload_registry_with(add_in_registry)
        self.check_comparator()
