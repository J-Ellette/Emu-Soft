# Hibernate Emulator - ORM and Query Builder

A lightweight emulation of **Hibernate**, the most popular Java ORM (Object-Relational Mapping) framework.

## Features

### Core ORM
- **Entity Management**: Persist, update, delete, and query entities
- **Session Management**: First-level cache and entity state tracking
- **Transaction Support**: ACID transaction management
- **Lazy Loading**: Proxy-based lazy loading (simulated)
- **Cascade Operations**: Propagate operations to related entities

### Query Capabilities
- **HQL (Hibernate Query Language)**: Object-oriented query language
- **Criteria API**: Type-safe programmatic queries
- **Named Queries**: Predefined reusable queries
- **Native SQL**: Execute raw SQL when needed

### Caching
- **First-Level Cache**: Session-scoped cache
- **Entity State Management**: Track entity lifecycle
- **Cache Operations**: Flush, clear, evict

### Configuration
- **Flexible Configuration**: Properties-based configuration
- **Entity Mapping**: Annotation-based entity mapping
- **Session Factory**: Centralized configuration and session management

## What It Emulates

This tool emulates core functionality of [Hibernate ORM](https://hibernate.org/), the de facto standard for ORM in Java applications.

### Core Components Implemented

1. **Configuration**
   - Property-based configuration
   - Entity class registration
   - SessionFactory building

2. **Session Management**
   - Session lifecycle
   - First-level cache
   - Entity state tracking

3. **Transaction Management**
   - Begin, commit, rollback
   - Transaction state tracking

4. **CRUD Operations**
   - save() / persist()
   - get() / load()
   - update() / merge()
   - delete()

5. **Querying**
   - HQL queries
   - Criteria API
   - Named and positional parameters

6. **Caching**
   - First-level (session) cache
   - Cache management operations

## Usage

### Basic Configuration

```java
import hibernate_emulator.*;

// Create configuration
Configuration config = new Configuration()
    .setProperty("hibernate.connection.url", "jdbc:mysql://localhost:3306/mydb")
    .setProperty("hibernate.connection.username", "user")
    .setProperty("hibernate.connection.password", "pass")
    .setProperty("hibernate.dialect", "org.hibernate.dialect.MySQLDialect")
    .setProperty("hibernate.show_sql", "true")
    .setProperty("hibernate.hbm2ddl.auto", "update");

// Add entity classes
config.addAnnotatedClass(User.class);
config.addAnnotatedClass(Order.class);

// Build SessionFactory
SessionFactory sessionFactory = config.buildSessionFactory();
```

### Entity Definition

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = "AUTO")
    private Long id;
    
    @Column(name = "username")
    private String username;
    
    @Column(name = "email")
    private String email;
    
    private int age;
    
    // Getters and setters
}
```

### CRUD Operations

```java
// Open session
Session session = sessionFactory.openSession();
Transaction tx = session.beginTransaction();

try {
    // Create
    User user = new User();
    user.setUsername("john_doe");
    user.setEmail("john@example.com");
    user.setAge(25);
    session.save(user);
    
    // Read
    User foundUser = session.get(User.class, 1L);
    
    // Update
    foundUser.setAge(26);
    session.update(foundUser);
    
    // Delete
    session.delete(foundUser);
    
    tx.commit();
} catch (Exception e) {
    if (tx != null) tx.rollback();
    e.printStackTrace();
} finally {
    session.close();
}
```

### HQL Queries

```java
Session session = sessionFactory.openSession();

// Simple HQL query
Query<User> query1 = session.createQuery("FROM User", User.class);
List<User> users = query1.list();

// Query with named parameter
Query<User> query2 = session.createQuery(
    "FROM User WHERE age > :minAge", User.class
);
query2.setParameter("minAge", 18);
List<User> adults = query2.list();

// Query with positional parameter
Query<User> query3 = session.createQuery(
    "FROM User WHERE username = ?1", User.class
);
query3.setParameter(1, "john_doe");
User user = query3.uniqueResult();

// Update query
Query updateQuery = session.createQuery(
    "UPDATE User SET status = :status WHERE age < :age"
);
updateQuery.setParameter("status", "inactive");
updateQuery.setParameter("age", 18);
int rowsAffected = updateQuery.executeUpdate();

session.close();
```

### Criteria API

```java
Session session = sessionFactory.openSession();

// Create criteria
Criteria<User> criteria = session.createCriteria(User.class);

// Add restrictions
criteria.add(Criterion.eq("status", "active"))
       .add(Criterion.gt("age", 18))
       .add(Criterion.like("username", "john%"));

// Add ordering
criteria.addOrder(Order.desc("createdDate"))
       .addOrder(Order.asc("username"));

// Pagination
criteria.setFirstResult(0)
       .setMaxResults(10);

// Execute
List<User> results = criteria.list();

session.close();
```

### Transaction Management

```java
Session session = sessionFactory.openSession();
Transaction tx = null;

try {
    tx = session.beginTransaction();
    
    // Perform operations
    User user1 = new User();
    session.save(user1);
    
    User user2 = new User();
    session.save(user2);
    
    // Commit transaction
    tx.commit();
} catch (Exception e) {
    if (tx != null && tx.isActive()) {
        tx.rollback();
    }
    e.printStackTrace();
} finally {
    session.close();
}
```

### Caching Operations

```java
Session session = sessionFactory.openSession();
Transaction tx = session.beginTransaction();

// Save entity (goes to first-level cache)
User user = new User();
session.save(user);

// Get from cache (no database hit)
User cachedUser = session.get(User.class, user.getId());

// Flush pending changes to database
session.flush();

// Evict specific entity from cache
session.evict(user);

// Clear entire session cache
session.clear();

// Refresh entity from database
session.refresh(user);

tx.commit();
session.close();
```

### Session Management Patterns

```java
// Basic pattern
Session session = sessionFactory.openSession();
try {
    // Use session
} finally {
    session.close();
}

// With transaction
Session session = sessionFactory.openSession();
Transaction tx = session.beginTransaction();
try {
    // Operations
    tx.commit();
} catch (Exception e) {
    tx.rollback();
    throw e;
} finally {
    session.close();
}

// Current session (thread-bound)
Session session = sessionFactory.getCurrentSession();
// Auto-closed at transaction end
```

## API Reference

### Configuration
- `setProperty(name, value)` - Set configuration property
- `addAnnotatedClass(Class)` - Register entity class
- `buildSessionFactory()` - Create SessionFactory

### SessionFactory
- `openSession()` - Open new session
- `getCurrentSession()` - Get thread-bound session
- `close()` - Close factory
- `isClosed()` - Check if closed

### Session
- `beginTransaction()` - Start transaction
- `getTransaction()` - Get current transaction
- `save(entity)` - Persist new entity
- `persist(entity)` - Persist entity
- `get(Class, id)` - Load entity by ID
- `load(Class, id)` - Load entity (lazy)
- `update(entity)` - Update entity
- `merge(entity)` - Merge detached entity
- `delete(entity)` - Remove entity
- `refresh(entity)` - Reload from database
- `createQuery(hql, Class)` - Create HQL query
- `createCriteria(Class)` - Create Criteria query
- `flush()` - Sync with database
- `clear()` - Clear cache
- `evict(entity)` - Remove from cache
- `close()` - Close session
- `isOpen()` - Check if open

### Transaction
- `begin()` - Begin transaction
- `commit()` - Commit transaction
- `rollback()` - Rollback transaction
- `isActive()` - Check if active

### Query<T>
- `setParameter(name, value)` - Set named parameter
- `setParameter(position, value)` - Set positional parameter
- `list()` - Get result list
- `uniqueResult()` - Get single result
- `executeUpdate()` - Execute update/delete

### Criteria<T>
- `add(Criterion)` - Add restriction
- `addOrder(Order)` - Add ordering
- `setMaxResults(int)` - Set max results
- `setFirstResult(int)` - Set offset
- `list()` - Execute query
- `uniqueResult()` - Get single result

### Criterion (Restrictions)
- `eq(property, value)` - Equals
- `ne(property, value)` - Not equals
- `gt(property, value)` - Greater than
- `lt(property, value)` - Less than
- `like(property, pattern)` - Like pattern

### Order
- `asc(property)` - Ascending order
- `desc(property)` - Descending order

## Annotations

- `@Entity` - Mark class as entity
- `@Table(name)` - Specify table name
- `@Id` - Mark identifier field
- `@GeneratedValue(strategy)` - Auto-generate ID
- `@Column(name)` - Specify column mapping

## Testing

Compile and run tests:

```bash
javac -d bin hibernate_emulator/*.java
java -cp bin hibernate_emulator.TestHibernateEmulator
```

Tests cover:
- Configuration and SessionFactory
- Session lifecycle
- Transaction management
- CRUD operations
- HQL queries
- Criteria API
- Caching operations

## Limitations

This is an educational emulation with limitations:

1. **No Database**: Doesn't connect to actual database
2. **Simplified Annotations**: Basic annotation support
3. **No Relationships**: OneToMany, ManyToOne not implemented
4. **No Lazy Loading**: Proxy mechanism simplified
5. **No Second-Level Cache**: Only first-level cache
6. **No Query Cache**: Query results not cached
7. **Limited HQL**: Basic HQL parsing only
8. **No Schema Generation**: DDL operations not implemented
9. **No Validators**: Bean validation not included
10. **No Interceptors**: Lifecycle interceptors not implemented

## Real-World Hibernate

To use real Hibernate, add Maven dependency:

```xml
<dependency>
    <groupId>org.hibernate</groupId>
    <artifactId>hibernate-core</artifactId>
    <version>6.3.1.Final</version>
</dependency>
```

## Use Cases

- Learning ORM concepts
- Understanding Hibernate architecture
- Testing without database
- Educational purposes
- Prototyping data layers
- Interview preparation

## Complexity

**Implementation Complexity**: Medium-High

This emulator involves:
- Entity lifecycle management
- Transaction coordination
- Query parsing and execution
- Caching strategies
- Session management
- Object-relational mapping

## Comparison with Real Hibernate

### Similarities
- Session and SessionFactory pattern
- Transaction management
- HQL syntax
- Criteria API structure
- Annotation-based mapping
- Cache concept

### Differences
- Real Hibernate connects to databases
- Real Hibernate has comprehensive ORM features
- Real Hibernate supports all JPA annotations
- Real Hibernate has advanced caching
- Real Hibernate generates SQL
- Real Hibernate supports relationships and associations

## Dependencies

- Java 8+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
