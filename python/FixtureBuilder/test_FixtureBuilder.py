"""
Developed by PowerShield, as an alternative to Factory Boy
"""

#!/usr/bin/env python3
"""
Tests for factory_boy emulator
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from factory_boy_emulator_tool.factory_boy_emulator import (
    Factory, Sequence, Faker, SubFactory, LazyAttribute,
    lazy_attribute, sequence, faker, subfactory
)


# Test models
class User:
    def __init__(self, username, email, first_name='', last_name='', is_active=True, age=None):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.age = age
    
    def __repr__(self):
        return f"User({self.username})"


class Post:
    def __init__(self, title, content, author=None):
        self.title = title
        self.content = content
        self.author = author
    
    def __repr__(self):
        return f"Post({self.title})"


# Test factories
class UserFactory(Factory):
    class Meta:
        model = User
    
    username = Sequence(lambda n: f"user{n}")
    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = Faker('name')
    last_name = 'Doe'
    is_active = True


class PostFactory(Factory):
    class Meta:
        model = Post
    
    title = Sequence(lambda n: f"Post {n}")
    content = Faker('text')
    author = SubFactory(UserFactory)


def test_basic_creation():
    """Test basic factory instance creation."""
    print("Testing basic creation...")
    user = UserFactory.create()
    assert hasattr(user, 'username')
    assert hasattr(user, 'email')
    assert user.username.startswith('user')
    assert user.is_active is True
    print("  ✓ Basic creation works")


def test_sequence():
    """Test sequence generation."""
    print("Testing sequences...")
    UserFactory.reset_sequence()
    user1 = UserFactory.create()
    user2 = UserFactory.create()
    user3 = UserFactory.create()
    
    assert user1.username == 'user0'
    assert user2.username == 'user1'
    assert user3.username == 'user2'
    assert user1.email == 'user0@example.com'
    assert user2.email == 'user1@example.com'
    print("  ✓ Sequences work correctly")


def test_override_attributes():
    """Test overriding factory attributes."""
    print("Testing attribute overrides...")
    user = UserFactory.create(username='custom_user', email='custom@example.com')
    assert user.username == 'custom_user'
    assert user.email == 'custom@example.com'
    print("  ✓ Attribute overrides work")


def test_faker():
    """Test faker data generation."""
    print("Testing Faker...")
    user = UserFactory.create()
    assert len(user.first_name) > 0
    assert user.first_name != 'Faker(name)'  # Should be actual name
    print(f"  Generated name: {user.first_name}")
    print("  ✓ Faker works")


def test_build_vs_create():
    """Test build and create methods."""
    print("Testing build vs create...")
    built_user = UserFactory.build()
    created_user = UserFactory.create()
    
    assert isinstance(built_user, User)
    assert isinstance(created_user, User)
    assert hasattr(built_user, 'username')
    assert hasattr(created_user, 'username')
    print("  ✓ Both build and create work")


def test_batch_creation():
    """Test batch creation of instances."""
    print("Testing batch creation...")
    users = UserFactory.create_batch(5)
    assert len(users) == 5
    assert all(isinstance(u, User) for u in users)
    
    # Check that usernames are unique
    usernames = [u.username for u in users]
    assert len(set(usernames)) == 5
    print(f"  Created {len(users)} users")
    print("  ✓ Batch creation works")


def test_subfactory():
    """Test subfactory relationships."""
    print("Testing subfactory...")
    post = PostFactory.create()
    
    assert isinstance(post, Post)
    assert hasattr(post, 'author')
    assert isinstance(post.author, User)
    assert hasattr(post.author, 'username')
    print(f"  Post: {post.title} by {post.author.username}")
    print("  ✓ SubFactory works")


def test_lazy_attribute():
    """Test lazy attributes."""
    print("Testing lazy attributes...")
    
    class UserWithFullName(Factory):
        class Meta:
            model = User
        
        username = Sequence(lambda n: f"user{n}")
        email = Sequence(lambda n: f"user{n}@example.com")
        first_name = 'John'
        last_name = 'Doe'
        age = LazyAttribute(lambda stub: len(stub.username) * 5)
    
    user = UserWithFullName.create()
    # username will be like "user0" (5 chars), so age should be 25
    assert user.age == len(user.username) * 5
    print(f"  User {user.username} has age {user.age}")
    print("  ✓ LazyAttribute works")


def test_stub():
    """Test stub creation."""
    print("Testing stub creation...")
    stub = UserFactory.stub()
    
    assert hasattr(stub, 'username')
    assert hasattr(stub, 'email')
    assert stub.username.startswith('user')
    print("  ✓ Stub creation works")


def test_reset_sequence():
    """Test resetting sequences."""
    print("Testing sequence reset...")
    UserFactory.reset_sequence()
    user1 = UserFactory.create()
    assert user1.username == 'user0'
    
    user2 = UserFactory.create()
    assert user2.username == 'user1'
    
    UserFactory.reset_sequence(value=10)
    user3 = UserFactory.create()
    assert user3.username == 'user10'
    print("  ✓ Sequence reset works")


def test_faker_providers():
    """Test various faker providers."""
    print("Testing Faker providers...")
    
    class TestFactory(Factory):
        name = Faker('name')
        email = Faker('email')
        url = Faker('url')
        address = Faker('address')
        phone = Faker('phone_number')
        company = Faker('company')
        date = Faker('date')
        datetime = Faker('datetime')
        text = Faker('text', max_nb_chars=50)
        random_int = Faker('random_int', min=1, max=10)
    
    obj = TestFactory.stub()
    
    assert len(obj.name) > 0
    assert '@' in obj.email
    assert obj.url.startswith('http')
    assert len(obj.address) > 0
    assert len(obj.phone) > 0
    assert len(obj.company) > 0
    assert obj.date is not None
    assert obj.datetime is not None
    assert len(obj.text) <= 50
    assert 1 <= obj.random_int <= 10
    
    print(f"  Name: {obj.name}")
    print(f"  Email: {obj.email}")
    print(f"  URL: {obj.url}")
    print(f"  Company: {obj.company}")
    print("  ✓ All Faker providers work")


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing factory_boy Emulator")
    print("=" * 60)
    
    tests = [
        test_basic_creation,
        test_sequence,
        test_override_attributes,
        test_faker,
        test_build_vs_create,
        test_batch_creation,
        test_subfactory,
        test_lazy_attribute,
        test_stub,
        test_reset_sequence,
        test_faker_providers,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            raise
        except Exception as e:
            print(f"  ✗ {test.__name__} error: {e}")
            raise
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
