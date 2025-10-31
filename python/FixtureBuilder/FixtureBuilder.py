#!/usr/bin/env python3
"""
Developed by PowerShield, as an alternative to factory_boy

factory_boy Emulator - Test Fixture Replacement

Emulates factory_boy functionality for creating test fixtures without external dependencies.
factory_boy is a fixtures replacement tool that helps create model instances for testing.

Reference: https://factoryboy.readthedocs.io/
"""

import random
import string
from typing import Any, Dict, List, Callable, Optional, Type
from datetime import datetime, timedelta
import inspect


class LazyAttribute:
    """Represents an attribute that will be computed lazily."""
    
    def __init__(self, func: Callable):
        self.func = func
    
    def evaluate(self, instance, stub):
        """Evaluate the lazy attribute."""
        return self.func(stub)


class Sequence:
    """Represents a sequential value generator."""
    
    def __init__(self, func: Callable[[int], Any], start: int = 0):
        self.func = func
        self.counter = start
    
    def next(self):
        """Get the next value in the sequence."""
        value = self.func(self.counter)
        self.counter += 1
        return value


class SubFactory:
    """Represents a reference to another factory."""
    
    def __init__(self, factory_class, **kwargs):
        self.factory_class = factory_class
        self.kwargs = kwargs
    
    def create(self):
        """Create an instance using the sub-factory."""
        return self.factory_class.create(**self.kwargs)


class Faker:
    """Simple faker for generating random data."""
    
    def __init__(self, provider: str, **kwargs):
        self.provider = provider
        self.kwargs = kwargs
    
    def generate(self):
        """Generate fake data based on provider."""
        if self.provider == 'name':
            return self._generate_name()
        elif self.provider == 'email':
            return self._generate_email()
        elif self.provider == 'text':
            return self._generate_text()
        elif self.provider == 'url':
            return self._generate_url()
        elif self.provider == 'address':
            return self._generate_address()
        elif self.provider == 'phone_number':
            return self._generate_phone()
        elif self.provider == 'company':
            return self._generate_company()
        elif self.provider == 'date':
            return self._generate_date()
        elif self.provider == 'datetime':
            return self._generate_datetime()
        elif self.provider == 'random_int':
            min_val = self.kwargs.get('min', 0)
            max_val = self.kwargs.get('max', 100)
            return random.randint(min_val, max_val)
        else:
            return f"fake_{self.provider}"
    
    def _generate_name(self):
        first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller']
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_email(self):
        domains = ['example.com', 'test.com', 'demo.org', 'sample.net']
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"{username}@{random.choice(domains)}"
    
    def _generate_text(self):
        length = self.kwargs.get('max_nb_chars', 200)
        words = ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit']
        text = ' '.join(random.choices(words, k=min(length // 6, 50)))
        return text[:length]
    
    def _generate_url(self):
        domains = ['example.com', 'test.com', 'demo.org']
        path = ''.join(random.choices(string.ascii_lowercase, k=8))
        return f"https://{random.choice(domains)}/{path}"
    
    def _generate_address(self):
        streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Pine Rd']
        cities = ['Springfield', 'Portland', 'Austin', 'Seattle', 'Boston']
        return f"{random.randint(1, 9999)} {random.choice(streets)}, {random.choice(cities)}"
    
    def _generate_phone(self):
        return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    def _generate_company(self):
        names = ['Tech', 'Soft', 'Data', 'Cloud', 'Web', 'Digital']
        suffixes = ['Corp', 'Inc', 'LLC', 'Solutions', 'Systems']
        return f"{random.choice(names)}{random.choice(suffixes)}"
    
    def _generate_date(self):
        days_ago = random.randint(0, 365)
        return (datetime.now() - timedelta(days=days_ago)).date()
    
    def _generate_datetime(self):
        days_ago = random.randint(0, 365)
        hours_ago = random.randint(0, 24)
        return datetime.now() - timedelta(days=days_ago, hours=hours_ago)


class FactoryStub:
    """Stub object that holds attribute values during factory build."""
    
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


class FactoryOptions:
    """Options for a factory."""
    
    def __init__(self, model=None, abstract=False):
        self.model = model
        self.abstract = abstract


class FactoryMetaclass(type):
    """Metaclass for Factory that processes declarations."""
    
    def __new__(mcs, name, bases, attrs):
        # Extract Meta class if present
        meta = attrs.pop('Meta', None)
        
        # Create the new class
        cls = super().__new__(mcs, name, bases, attrs)
        
        # Process Meta options
        if meta:
            cls._meta = FactoryOptions(
                model=getattr(meta, 'model', None),
                abstract=getattr(meta, 'abstract', False)
            )
        else:
            cls._meta = FactoryOptions()
        
        # Collect declarations from class and bases
        declarations = {}
        for base in reversed(bases):
            if hasattr(base, '_declarations'):
                declarations.update(base._declarations)
        
        # Add this class's declarations
        for key, value in list(attrs.items()):
            if not key.startswith('_') and key not in ('Meta', 'create', 'build', 'build_batch', 'create_batch', 'stub', 'reset_sequence'):
                if isinstance(value, (LazyAttribute, Sequence, SubFactory, Faker)):
                    declarations[key] = value
                    delattr(cls, key)
                elif not callable(value):
                    declarations[key] = value
        
        cls._declarations = declarations
        cls._sequences = {}
        
        return cls


class Factory(metaclass=FactoryMetaclass):
    """Base factory class for creating test fixtures."""
    
    class Meta:
        abstract = True
    
    @classmethod
    def _build(cls, **kwargs):
        """Build an instance without saving/persisting."""
        # Merge declarations with overrides
        stub_attrs = {}
        
        # Process declarations
        for key, value in cls._declarations.items():
            if key in kwargs:
                stub_attrs[key] = kwargs[key]
            elif isinstance(value, Sequence):
                if key not in cls._sequences:
                    cls._sequences[key] = value
                stub_attrs[key] = cls._sequences[key].next()
            elif isinstance(value, SubFactory):
                stub_attrs[key] = value.create()
            elif isinstance(value, Faker):
                stub_attrs[key] = value.generate()
            else:
                stub_attrs[key] = value
        
        # Add any extra kwargs
        for key, value in kwargs.items():
            if key not in stub_attrs:
                stub_attrs[key] = value
        
        # Create stub for lazy attribute evaluation
        stub = FactoryStub(**stub_attrs)
        
        # Process lazy attributes
        final_attrs = {}
        for key, value in stub_attrs.items():
            if isinstance(cls._declarations.get(key), LazyAttribute):
                final_attrs[key] = cls._declarations[key].evaluate(None, stub)
            else:
                final_attrs[key] = value
        
        # Create the actual instance
        if cls._meta.model:
            instance = cls._meta.model(**final_attrs)
        else:
            instance = FactoryStub(**final_attrs)
        
        return instance
    
    @classmethod
    def build(cls, **kwargs):
        """Build a single instance."""
        return cls._build(**kwargs)
    
    @classmethod
    def create(cls, **kwargs):
        """Create a single instance (same as build in this emulator)."""
        return cls._build(**kwargs)
    
    @classmethod
    def build_batch(cls, size: int, **kwargs):
        """Build multiple instances."""
        return [cls.build(**kwargs) for _ in range(size)]
    
    @classmethod
    def create_batch(cls, size: int, **kwargs):
        """Create multiple instances."""
        return [cls.create(**kwargs) for _ in range(size)]
    
    @classmethod
    def stub(cls, **kwargs):
        """Create a stub (dictionary-like object) instead of model instance."""
        stub_attrs = {}
        
        for key, value in cls._declarations.items():
            if key in kwargs:
                stub_attrs[key] = kwargs[key]
            elif isinstance(value, Sequence):
                if key not in cls._sequences:
                    cls._sequences[key] = value
                stub_attrs[key] = cls._sequences[key].next()
            elif isinstance(value, SubFactory):
                stub_attrs[key] = value.create()
            elif isinstance(value, Faker):
                stub_attrs[key] = value.generate()
            else:
                stub_attrs[key] = value
        
        for key, value in kwargs.items():
            if key not in stub_attrs:
                stub_attrs[key] = value
        
        return FactoryStub(**stub_attrs)
    
    @classmethod
    def reset_sequence(cls, key: Optional[str] = None, value: int = 0):
        """Reset sequence counter(s)."""
        if key:
            if key in cls._sequences:
                cls._sequences[key].counter = value
        else:
            # Reset all sequences
            for seq in cls._sequences.values():
                seq.counter = value


# Convenience functions
def lazy_attribute(func):
    """Decorator to create a lazy attribute."""
    return LazyAttribute(func)


def sequence(func, start=0):
    """Create a sequence."""
    return Sequence(func, start)


def faker(provider, **kwargs):
    """Create a faker."""
    return Faker(provider, **kwargs)


def subfactory(factory_class, **kwargs):
    """Create a subfactory."""
    return SubFactory(factory_class, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Define a simple model
    class User:
        def __init__(self, username, email, first_name, last_name, is_active=True):
            self.username = username
            self.email = email
            self.first_name = first_name
            self.last_name = last_name
            self.is_active = is_active
        
        def __repr__(self):
            return f"User(username={self.username}, email={self.email})"
    
    # Define a factory
    class UserFactory(Factory):
        class Meta:
            model = User
        
        username = Sequence(lambda n: f"user{n}")
        email = Sequence(lambda n: f"user{n}@example.com")
        first_name = Faker('name')
        last_name = 'Doe'
        is_active = True
    
    # Test factory
    print("Creating users with factory...")
    user1 = UserFactory.create()
    print(f"User 1: {user1}")
    print(f"  Username: {user1.username}")
    print(f"  Email: {user1.email}")
    print(f"  Name: {user1.first_name} {user1.last_name}")
    
    user2 = UserFactory.create(first_name="Bob")
    print(f"\nUser 2: {user2}")
    print(f"  Username: {user2.username}")
    print(f"  Email: {user2.email}")
    print(f"  Name: {user2.first_name} {user2.last_name}")
    
    # Create batch
    users = UserFactory.create_batch(3)
    print(f"\nCreated batch of {len(users)} users:")
    for user in users:
        print(f"  - {user}")
    
    print("\n✓ factory_boy emulator working correctly!")
